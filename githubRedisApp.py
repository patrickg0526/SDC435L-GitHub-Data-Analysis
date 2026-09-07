#####################################################################
# Name: Patrick Gonzalez
# Date: 09/06/2026
# Assignment: 1.6 Group Project - Redis Integration (Part 1)
# Purpose: Menu-driven Python application that imports GitHub Archive
#          commit and language data into a Redis key-value database,
#          performs CRUD operations on commit records, and offers
#          three analysis features: programming language popularity,
#          a contributor's commit history, and an ASCII-bar
#          visualization of commit activity by author for a given
#          repository.
#####################################################################

import json
import redis

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

COMMITS_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Commits.json'
LANGUAGES_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Languages.json'
# NOTE: Commits.json and Languages.json are large (~23MB / ~436MB), so
# only a manageable sample of each is imported for this part of the
# project rather than the entire file.
COMMIT_IMPORT_LIMIT = 2000
LANGUAGE_IMPORT_LIMIT = 5000


def import_commits(path=COMMITS_FILE, limit=COMMIT_IMPORT_LIMIT):
    # *Read JSON-formatted commit data from the GitHub Archive and store it in Redis
    print(f"Importing up to {limit} commits from {path} ...")
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if count >= limit:
                break
            data = json.loads(line)
            commit_hash = data.get("commit")
            if not commit_hash:
                continue
            author = data.get("author", {})
            repos = data.get("repo_name") or []
            repo_name = repos[0] if repos else "unknown"
            key = f"commit:{commit_hash}"
            r.hset(key, mapping={
                "author_name": author.get("name", "unknown"),
                "author_email": author.get("email", "unknown"),
                "repo_name": repo_name,
                "subject": (data.get("subject") or "")[:200],
            })
            r.sadd(f"repo:{repo_name}", commit_hash)
            r.sadd(f"author:{author.get('email', 'unknown')}", commit_hash)
            count += 1
    print(f"Imported {count} commit records into Redis.")


def import_languages(path=LANGUAGES_FILE, limit=LANGUAGE_IMPORT_LIMIT):
    # *Read JSON-formatted language data and aggregate byte totals in Redis
    print(f"Importing language stats from up to {limit} repositories ...")
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if count >= limit:
                break
            data = json.loads(line)
            for lang in data.get("language", []):
                name = lang.get("name")
                try:
                    size = int(lang.get("bytes", 0))
                except (TypeError, ValueError):
                    size = 0
                if name:
                    r.zincrby("languageBytes", size, name)
            count += 1
    print(f"Aggregated language stats from {count} repositories.\n")


# ---------------- CRUD operations on commit records ----------------

def create_commit():
    # *Create a new commit record in the Redis database
    commit_hash = input("Enter a commit hash/id for the new record: ").strip()
    author_name = input("Author name: ").strip()
    author_email = input("Author email: ").strip()
    repo_name = input("Repository name: ").strip()
    subject = input("Commit subject/message: ").strip()
    key = f"commit:{commit_hash}"
    r.hset(key, mapping={
        "author_name": author_name,
        "author_email": author_email,
        "repo_name": repo_name,
        "subject": subject,
    })
    r.sadd(f"repo:{repo_name}", commit_hash)
    r.sadd(f"author:{author_email}", commit_hash)
    print(f"Created commit record '{commit_hash}'.")


def read_commit():
    # *Retrieve a commit record from the Redis database
    commit_hash = input("Enter the commit hash/id to view: ").strip()
    key = f"commit:{commit_hash}"
    data = r.hgetall(key)
    if not data:
        print(f"No commit record found for '{commit_hash}'.")
        return
    print(f"\nCommit {commit_hash}:")
    for field, value in data.items():
        print(f"  {field}: {value}")


def update_commit():
    # *Update a commit record's subject/message in the Redis database
    commit_hash = input("Enter the commit hash/id to update: ").strip()
    key = f"commit:{commit_hash}"
    if not r.exists(key):
        print(f"No commit record found for '{commit_hash}'.")
        return
    new_subject = input("Enter the new subject/message: ").strip()
    r.hset(key, "subject", new_subject)
    print(f"Updated subject for commit '{commit_hash}'.")


def delete_commit():
    # *Delete a commit record from the Redis database
    commit_hash = input("Enter the commit hash/id to delete: ").strip()
    key = f"commit:{commit_hash}"
    data = r.hgetall(key)
    if not data:
        print(f"No commit record found for '{commit_hash}'.")
        return
    repo_name = data.get("repo_name", "unknown")
    author_email = data.get("author_email", "unknown")
    r.delete(key)
    r.srem(f"repo:{repo_name}", commit_hash)
    r.srem(f"author:{author_email}", commit_hash)
    print(f"Deleted commit record '{commit_hash}'.")


# ---------------- Feature 1: Programming language popularity ----------------

def feature_language_popularity():
    # *Feature 1: Show the most popular programming languages by total bytes
    top_n = input("How many top languages would you like to see? (default 10): ").strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    results = r.zrevrange("languageBytes", 0, top_n - 1, withscores=True)
    if not results:
        print("No language data available. Did you run the import step?")
        return
    print(f"\nTop {top_n} languages by total bytes across sampled repositories:")
    for rank, (name, score) in enumerate(results, start=1):
        print(f"  {rank}. {name} - {int(score):,} bytes")


# ---------------- Feature 2: A contributor's commit history ----------------

def feature_author_history():
    # *Feature 2: Show a contributor's commits based on their author email
    email = input("Enter the author's email to look up: ").strip()
    commit_hashes = r.smembers(f"author:{email}")
    if not commit_hashes:
        print(f"No commits found for author '{email}'.")
        return
    print(f"\n{email} has {len(commit_hashes)} commit(s) in the database:")
    for h in list(commit_hashes)[:20]:
        data = r.hgetall(f"commit:{h}")
        print(f"  [{h[:10]}] ({data.get('repo_name', 'unknown')}) {data.get('subject', '')}")
    if len(commit_hashes) > 20:
        print(f"  ... and {len(commit_hashes) - 20} more.")


# ---------------- Feature 3: Commit activity visualization ----------------

def feature_repo_visualization():
    # *Feature 3: ASCII bar-chart visualization of commit activity by author for a repository
    repo_name = input("Enter a repository name to visualize (e.g. facebook/react): ").strip()
    commit_hashes = r.smembers(f"repo:{repo_name}")
    if not commit_hashes:
        print(f"No commits found for repository '{repo_name}'.")
        return
    counts = {}
    for h in commit_hashes:
        author = r.hget(f"commit:{h}", "author_name") or "unknown"
        counts[author] = counts.get(author, 0) + 1
    print(f"\nCommit activity for '{repo_name}' ({len(commit_hashes)} commit(s) total):")
    for author, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        bar = "#" * count
        print(f"  {author:<25} {bar} ({count})")


# ---------------- Menu ----------------

def print_menu():
    print("\n===== GitHub Archive / Redis CRUD Menu =====")
    print("1. Create a commit record")
    print("2. Read a commit record")
    print("3. Update a commit record")
    print("4. Delete a commit record")
    print("5. Feature: Programming language popularity")
    print("6. Feature: A contributor's commit history")
    print("7. Feature: Commit activity visualization for a repo")
    print("8. Exit")


def main():
    import_commits()
    import_languages()
    while True:
        print_menu()
        choice = input("Select an option (1-8): ").strip()
        if choice == "1":
            create_commit()
        elif choice == "2":
            read_commit()
        elif choice == "3":
            update_commit()
        elif choice == "4":
            delete_commit()
        elif choice == "5":
            feature_language_popularity()
        elif choice == "6":
            feature_author_history()
        elif choice == "7":
            feature_repo_visualization()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid selection, please choose 1-8.")


if __name__ == "__main__":
    main()
