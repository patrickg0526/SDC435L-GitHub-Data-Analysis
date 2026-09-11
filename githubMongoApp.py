#####################################################################
# Name: Patrick Gonzalez
# Date: 09/10/2026
# Assignment: 2.3 Group Project - MongoDB Integration (Part 2)
# Purpose: Menu-driven Python application that imports GitHub Archive
#          commit and language data into a MongoDB database,
#          performs CRUD operations on commit documents, and offers
#          three analysis features: programming language popularity,
#          a contributor's commit history, and an ASCII-bar
#          visualization of commit activity by author for a given
#          repository.
#####################################################################

import json
import pymongo

# *Configure the database connection
print("Connecting to local Mongo database...")
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["GitHubArchive"]
commits = db["Commits"]
languages = db["Languages"]

COMMITS_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Commits.json'
LANGUAGES_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Languages.json'
# NOTE: Commits.json and Languages.json are large (~23MB / ~436MB), so
# only a manageable sample of each is imported for this part of the
# project rather than the entire file.
COMMIT_IMPORT_LIMIT = 2000
LANGUAGE_IMPORT_LIMIT = 5000


def import_commits(path=COMMITS_FILE, limit=COMMIT_IMPORT_LIMIT):
    # *Read JSON-formatted commit data from the GitHub Archive and store it in MongoDB
    print(f"Importing up to {limit} commits from {path} ...")
    commits.drop()
    count = 0
    docs = []
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
            docs.append({
                "commit_hash": commit_hash,
                "author_name": author.get("name", "unknown"),
                "author_email": author.get("email", "unknown"),
                "repo_name": repos[0] if repos else "unknown",
                "subject": (data.get("subject") or "")[:200],
            })
            count += 1
    if docs:
        commits.insert_many(docs)
    commits.create_index("commit_hash", unique=True)
    commits.create_index("repo_name")
    commits.create_index("author_email")
    print(f"Imported {count} commit records into MongoDB.")


def import_languages(path=LANGUAGES_FILE, limit=LANGUAGE_IMPORT_LIMIT):
    # *Read JSON-formatted language data and aggregate byte totals in MongoDB
    print(f"Importing language stats from up to {limit} repositories ...")
    languages.drop()
    totals = {}
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
                    totals[name] = totals.get(name, 0) + size
            count += 1
    if totals:
        languages.insert_many(
            [{"language": name, "totalBytes": total} for name, total in totals.items()]
        )
    print(f"Aggregated language stats from {count} repositories.\n")


# ---------------- CRUD operations on commit documents ----------------

def create_commit():
    # *Create a new commit document in the MongoDB database
    commit_hash = input("Enter a commit hash/id for the new record: ").strip()
    doc = {
        "commit_hash": commit_hash,
        "author_name": input("Author name: ").strip(),
        "author_email": input("Author email: ").strip(),
        "repo_name": input("Repository name: ").strip(),
        "subject": input("Commit subject/message: ").strip(),
    }
    commits.insert_one(doc)
    print(f"Created commit document '{commit_hash}'.")


def read_commit():
    # *Retrieve a commit document from the MongoDB database
    commit_hash = input("Enter the commit hash/id to view: ").strip()
    doc = commits.find_one({"commit_hash": commit_hash}, {"_id": False})
    if not doc:
        print(f"No commit document found for '{commit_hash}'.")
        return
    print(f"\nCommit {commit_hash}:")
    for field, value in doc.items():
        print(f"  {field}: {value}")


def update_commit():
    # *Update a commit document's subject/message in the MongoDB database
    commit_hash = input("Enter the commit hash/id to update: ").strip()
    if not commits.find_one({"commit_hash": commit_hash}):
        print(f"No commit document found for '{commit_hash}'.")
        return
    new_subject = input("Enter the new subject/message: ").strip()
    commits.update_one({"commit_hash": commit_hash}, {"$set": {"subject": new_subject}})
    print(f"Updated subject for commit '{commit_hash}'.")


def delete_commit():
    # *Delete a commit document from the MongoDB database
    commit_hash = input("Enter the commit hash/id to delete: ").strip()
    result = commits.delete_one({"commit_hash": commit_hash})
    if result.deleted_count:
        print(f"Deleted commit document '{commit_hash}'.")
    else:
        print(f"No commit document found for '{commit_hash}'.")


# ---------------- Feature 1: Programming language popularity ----------------

def feature_language_popularity():
    # *Feature 1: Show the most popular programming languages by total bytes
    top_n = input("How many top languages would you like to see? (default 10): ").strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    results = list(languages.find().sort("totalBytes", pymongo.DESCENDING).limit(top_n))
    if not results:
        print("No language data available. Did you run the import step?")
        return
    print(f"\nTop {top_n} languages by total bytes across sampled repositories:")
    for rank, doc in enumerate(results, start=1):
        print(f"  {rank}. {doc['language']} - {doc['totalBytes']:,} bytes")


# ---------------- Feature 2: A contributor's commit history ----------------

def feature_author_history():
    # *Feature 2: Show a contributor's commits based on their author email
    email = input("Enter the author's email to look up: ").strip()
    results = list(commits.find({"author_email": email}))
    if not results:
        print(f"No commits found for author '{email}'.")
        return
    print(f"\n{email} has {len(results)} commit(s) in the database:")
    for doc in results[:20]:
        print(f"  [{doc['commit_hash'][:10]}] ({doc['repo_name']}) {doc['subject']}")
    if len(results) > 20:
        print(f"  ... and {len(results) - 20} more.")


# ---------------- Feature 3: Commit activity visualization ----------------

def feature_repo_visualization():
    # *Feature 3: ASCII bar-chart visualization of commit activity by author for a repository
    repo_name = input("Enter a repository name to visualize (e.g. facebook/react): ").strip()
    results = list(commits.find({"repo_name": repo_name}))
    if not results:
        print(f"No commits found for repository '{repo_name}'.")
        return
    counts = {}
    for doc in results:
        author = doc.get("author_name", "unknown")
        counts[author] = counts.get(author, 0) + 1
    print(f"\nCommit activity for '{repo_name}' ({len(results)} commit(s) total):")
    for author, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        bar = "#" * count
        print(f"  {author:<25} {bar} ({count})")


# ---------------- Menu ----------------

def print_menu():
    print("\n===== GitHub Archive / MongoDB CRUD Menu =====")
    print("1. Create a commit document")
    print("2. Read a commit document")
    print("3. Update a commit document")
    print("4. Delete a commit document")
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
