#####################################################################
# Name: Patrick Gonzalez
# Date: 09/23/2026
# Assignment: 4.3 Group Project - Neo4j Integration (Part 4)
# Purpose: Menu-driven Python application that imports GitHub Archive
#          commit and language data into a Neo4j graph database,
#          performs CRUD operations on commit nodes, and offers
#          three analysis features: programming language popularity,
#          a contributor's commit history, and an ASCII-bar
#          visualization of commit activity by author for a given
#          repository.
#####################################################################

import json
from neo4j import GraphDatabase

# *Configure the database connection
print("Connecting to local Neo4j database...")
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password1")
driver = GraphDatabase.driver(URI, auth=AUTH)
session = driver.session()

COMMITS_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Commits.json'
LANGUAGES_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Languages.json'
# NOTE: Commits.json and Languages.json are large (~23MB / ~436MB), so
# only a manageable sample of each is imported for this part of the
# project rather than the entire file.
COMMIT_IMPORT_LIMIT = 500
LANGUAGE_IMPORT_LIMIT = 5000


def import_commits(path=COMMITS_FILE, limit=COMMIT_IMPORT_LIMIT):
    # *Read JSON-formatted commit data from the GitHub Archive and store it in Neo4j as
    # Commit, Author, and Repo nodes connected by relationships
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
            subject = (data.get("subject") or "")[:200]
            author_email = author.get("email", "unknown")

            session.run(
                "MERGE (c:Commit {hash:$hash}) "
                "SET c.subject = $subject",
                hash=commit_hash, subject=subject,
            )
            session.run(
                "MERGE (a:Author {email:$email}) SET a.name = $name",
                email=author_email, name=author.get("name", "unknown"),
            )
            session.run(
                "MERGE (r:Repo {name:$repo})",
                repo=repo_name,
            )
            session.run(
                "MATCH (a:Author {email:$email}), (c:Commit {hash:$hash}) "
                "MERGE (a)-[:AUTHORED]->(c)",
                email=author_email, hash=commit_hash,
            )
            session.run(
                "MATCH (c:Commit {hash:$hash}), (r:Repo {name:$repo}) "
                "MERGE (c)-[:IN_REPO]->(r)",
                hash=commit_hash, repo=repo_name,
            )
            count += 1
    print(f"Imported {count} commit records into Neo4j.")


def import_languages(path=LANGUAGES_FILE, limit=LANGUAGE_IMPORT_LIMIT):
    # *Read JSON-formatted language data and aggregate byte totals, then store as Language nodes
    print(f"Importing language stats from up to {limit} repositories ...")
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
    for name, total in totals.items():
        session.run(
            "MERGE (l:Language {name:$name}) SET l.total_bytes = $bytes",
            name=name, bytes=total,
        )
    print(f"Aggregated language stats from {count} repositories.\n")


# ---------------- CRUD operations on commit nodes ----------------

def create_commit():
    # *Create a new commit node in the Neo4j database
    commit_hash = input("Enter a commit hash/id for the new record: ").strip()
    author_name = input("Author name: ").strip()
    author_email = input("Author email: ").strip()
    repo_name = input("Repository name: ").strip()
    subject = input("Commit subject/message: ").strip()
    session.run(
        "MERGE (c:Commit {hash:$hash}) SET c.subject = $subject "
        "MERGE (a:Author {email:$email}) SET a.name = $name "
        "MERGE (r:Repo {name:$repo}) "
        "MERGE (a)-[:AUTHORED]->(c) MERGE (c)-[:IN_REPO]->(r)",
        hash=commit_hash, subject=subject, email=author_email, name=author_name, repo=repo_name,
    )
    print(f"Created commit record '{commit_hash}'.")


def read_commit():
    # *Retrieve a commit node from the Neo4j database
    commit_hash = input("Enter the commit hash/id to view: ").strip()
    result = session.run(
        "MATCH (a:Author)-[:AUTHORED]->(c:Commit {hash:$hash})-[:IN_REPO]->(r:Repo) "
        "RETURN a.name AS author_name, a.email AS author_email, r.name AS repo_name, c.subject AS subject",
        hash=commit_hash,
    )
    record = result.single()
    if not record:
        print(f"No commit record found for '{commit_hash}'.")
        return
    print(f"\nCommit {commit_hash}:")
    print(f"  author_name: {record['author_name']}")
    print(f"  author_email: {record['author_email']}")
    print(f"  repo_name: {record['repo_name']}")
    print(f"  subject: {record['subject']}")


def update_commit():
    # *Update a commit node's subject/message in the Neo4j database
    commit_hash = input("Enter the commit hash/id to update: ").strip()
    existing = session.run("MATCH (c:Commit {hash:$hash}) RETURN c", hash=commit_hash).single()
    if not existing:
        print(f"No commit record found for '{commit_hash}'.")
        return
    new_subject = input("Enter the new subject/message: ").strip()
    session.run("MATCH (c:Commit {hash:$hash}) SET c.subject = $subject", hash=commit_hash, subject=new_subject)
    print(f"Updated subject for commit '{commit_hash}'.")


def delete_commit():
    # *Delete a commit node from the Neo4j database
    commit_hash = input("Enter the commit hash/id to delete: ").strip()
    existing = session.run("MATCH (c:Commit {hash:$hash}) RETURN c", hash=commit_hash).single()
    if not existing:
        print(f"No commit record found for '{commit_hash}'.")
        return
    session.run("MATCH (c:Commit {hash:$hash}) DETACH DELETE c", hash=commit_hash)
    print(f"Deleted commit record '{commit_hash}'.")


# ---------------- Feature 1: Programming language popularity ----------------

def feature_language_popularity():
    # *Feature 1: Show the most popular programming languages by total bytes
    top_n = input("How many top languages would you like to see? (default 10): ").strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    results = list(session.run("MATCH (l:Language) RETURN l.name AS name, l.total_bytes AS total_bytes"))
    if not results:
        print("No language data available. Did you run the import step?")
        return
    results.sort(key=lambda r: r["total_bytes"], reverse=True)
    print(f"\nTop {top_n} languages by total bytes across sampled repositories:")
    for rank, row in enumerate(results[:top_n], start=1):
        print(f"  {rank}. {row['name']} - {row['total_bytes']:,} bytes")


# ---------------- Feature 2: A contributor's commit history ----------------

def feature_author_history():
    # *Feature 2: Show a contributor's commits based on their author email
    email = input("Enter the author's email to look up: ").strip()
    results = list(session.run(
        "MATCH (a:Author {email:$email})-[:AUTHORED]->(c:Commit)-[:IN_REPO]->(r:Repo) "
        "RETURN c.hash AS hash, r.name AS repo, c.subject AS subject",
        email=email,
    ))
    if not results:
        print(f"No commits found for author '{email}'.")
        return
    print(f"\n{email} has {len(results)} commit(s) in the database:")
    for row in results[:20]:
        print(f"  [{row['hash'][:10]}] ({row['repo']}) {row['subject']}")
    if len(results) > 20:
        print(f"  ... and {len(results) - 20} more.")


# ---------------- Feature 3: Commit activity visualization ----------------

def feature_repo_visualization():
    # *Feature 3: ASCII bar-chart visualization of commit activity by author for a repository
    repo_name = input("Enter a repository name to visualize (e.g. facebook/react): ").strip()
    results = list(session.run(
        "MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:IN_REPO]->(r:Repo {name:$repo}) "
        "RETURN a.name AS author",
        repo=repo_name,
    ))
    if not results:
        print(f"No commits found for repository '{repo_name}'.")
        return
    counts = {}
    for row in results:
        author = row["author"] or "unknown"
        counts[author] = counts.get(author, 0) + 1
    print(f"\nCommit activity for '{repo_name}' ({len(results)} commit(s) total):")
    for author, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        bar = "#" * count
        print(f"  {author:<25} {bar} ({count})")


# ---------------- Menu ----------------

def print_menu():
    print("\n===== GitHub Archive / Neo4j CRUD Menu =====")
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
    session.close()
    driver.close()


if __name__ == "__main__":
    main()
