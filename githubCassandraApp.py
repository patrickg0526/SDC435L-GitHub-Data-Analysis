#####################################################################
# Name: Patrick Gonzalez
# Date: 09/15/2026
# Assignment: 3.3 Group Project - Cassandra Integration (Part 3)
# Purpose: Menu-driven Python application that imports GitHub Archive
#          commit and language data into a Cassandra database,
#          performs CRUD operations on commit records, and offers
#          three analysis features: programming language popularity,
#          a contributor's commit history, and an ASCII-bar
#          visualization of commit activity by author for a given
#          repository.
#####################################################################

import json
from cassandra.cluster import Cluster

# *Configure the database connection
print("Connecting to local Cassandra database...")
cluster = Cluster()
session = cluster.connect()

COMMITS_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Commits.json'
LANGUAGES_FILE = 'GitHubArchive-Dataset/GitHubArchive-Dataset/Languages.json'
# NOTE: Commits.json and Languages.json are large (~23MB / ~436MB), so
# only a manageable sample of each is imported for this part of the
# project rather than the entire file.
COMMIT_IMPORT_LIMIT = 2000
LANGUAGE_IMPORT_LIMIT = 5000


def create_keyspace_and_tables():
    # *Create the GitHubArchive keyspace and Commits/Languages tables
    keyspace = '''
        CREATE KEYSPACE IF NOT EXISTS GitHubArchive WITH replication =
        {'class':'SimpleStrategy','replication_factor':1};
        '''
    session.execute(keyspace)
    session.execute('USE GitHubArchive;')
    session.set_keyspace('githubarchive')

    commitsTable = '''
        CREATE TABLE IF NOT EXISTS Commits(
        commit_hash text PRIMARY KEY,
        author_name text,
        author_email text,
        repo_name text,
        subject text
        );
        '''
    session.execute(commitsTable)

    languagesTable = '''
        CREATE TABLE IF NOT EXISTS Languages(
        language text PRIMARY KEY,
        total_bytes bigint
        );
        '''
    session.execute(languagesTable)


def import_commits(path=COMMITS_FILE, limit=COMMIT_IMPORT_LIMIT):
    # *Read JSON-formatted commit data from the GitHub Archive and store it in Cassandra
    print(f"Importing up to {limit} commits from {path} ...")
    insertCommit = '''
        INSERT INTO Commits (commit_hash, author_name, author_email, repo_name, subject)
        VALUES (%s, %s, %s, %s, %s);
        '''
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
            session.execute(insertCommit, [
                commit_hash,
                author.get("name", "unknown"),
                author.get("email", "unknown"),
                repos[0] if repos else "unknown",
                (data.get("subject") or "")[:200],
            ])
            count += 1
    print(f"Imported {count} commit records into Cassandra.")


def import_languages(path=LANGUAGES_FILE, limit=LANGUAGE_IMPORT_LIMIT):
    # *Read JSON-formatted language data and aggregate byte totals, then store in Cassandra
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
    insertLanguage = 'INSERT INTO Languages (language, total_bytes) VALUES (%s, %s);'
    for name, total in totals.items():
        session.execute(insertLanguage, [name, total])
    print(f"Aggregated language stats from {count} repositories.\n")


# ---------------- CRUD operations on commit records ----------------

def create_commit():
    # *Create a new commit record in the Cassandra database
    commit_hash = input("Enter a commit hash/id for the new record: ").strip()
    author_name = input("Author name: ").strip()
    author_email = input("Author email: ").strip()
    repo_name = input("Repository name: ").strip()
    subject = input("Commit subject/message: ").strip()
    query = '''INSERT INTO Commits (commit_hash, author_name, author_email, repo_name, subject)
            VALUES (%s, %s, %s, %s, %s);'''
    session.execute(query, [commit_hash, author_name, author_email, repo_name, subject])
    print(f"Created commit record '{commit_hash}'.")


def read_commit():
    # *Retrieve a commit record from the Cassandra database
    commit_hash = input("Enter the commit hash/id to view: ").strip()
    query = 'SELECT * FROM Commits WHERE commit_hash = %s;'
    row = session.execute(query, [commit_hash]).one()
    if not row:
        print(f"No commit record found for '{commit_hash}'.")
        return
    print(f"\nCommit {commit_hash}:")
    print(f"  author_name: {row.author_name}")
    print(f"  author_email: {row.author_email}")
    print(f"  repo_name: {row.repo_name}")
    print(f"  subject: {row.subject}")


def update_commit():
    # *Update a commit record's subject/message in the Cassandra database
    commit_hash = input("Enter the commit hash/id to update: ").strip()
    existing = session.execute('SELECT commit_hash FROM Commits WHERE commit_hash = %s;', [commit_hash]).one()
    if not existing:
        print(f"No commit record found for '{commit_hash}'.")
        return
    new_subject = input("Enter the new subject/message: ").strip()
    session.execute('UPDATE Commits SET subject = %s WHERE commit_hash = %s;', [new_subject, commit_hash])
    print(f"Updated subject for commit '{commit_hash}'.")


def delete_commit():
    # *Delete a commit record from the Cassandra database
    commit_hash = input("Enter the commit hash/id to delete: ").strip()
    existing = session.execute('SELECT commit_hash FROM Commits WHERE commit_hash = %s;', [commit_hash]).one()
    if not existing:
        print(f"No commit record found for '{commit_hash}'.")
        return
    session.execute('DELETE FROM Commits WHERE commit_hash = %s;', [commit_hash])
    print(f"Deleted commit record '{commit_hash}'.")


# ---------------- Feature 1: Programming language popularity ----------------

def feature_language_popularity():
    # *Feature 1: Show the most popular programming languages by total bytes
    top_n = input("How many top languages would you like to see? (default 10): ").strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    results = list(session.execute('SELECT language, total_bytes FROM Languages;'))
    if not results:
        print("No language data available. Did you run the import step?")
        return
    results.sort(key=lambda r: r.total_bytes, reverse=True)
    print(f"\nTop {top_n} languages by total bytes across sampled repositories:")
    for rank, row in enumerate(results[:top_n], start=1):
        print(f"  {rank}. {row.language} - {row.total_bytes:,} bytes")


# ---------------- Feature 2: A contributor's commit history ----------------

def feature_author_history():
    # *Feature 2: Show a contributor's commits based on their author email
    email = input("Enter the author's email to look up: ").strip()
    query = 'SELECT * FROM Commits WHERE author_email = %s ALLOW FILTERING;'
    results = list(session.execute(query, [email]))
    if not results:
        print(f"No commits found for author '{email}'.")
        return
    print(f"\n{email} has {len(results)} commit(s) in the database:")
    for row in results[:20]:
        print(f"  [{row.commit_hash[:10]}] ({row.repo_name}) {row.subject}")
    if len(results) > 20:
        print(f"  ... and {len(results) - 20} more.")


# ---------------- Feature 3: Commit activity visualization ----------------

def feature_repo_visualization():
    # *Feature 3: ASCII bar-chart visualization of commit activity by author for a repository
    repo_name = input("Enter a repository name to visualize (e.g. facebook/react): ").strip()
    query = 'SELECT author_name FROM Commits WHERE repo_name = %s ALLOW FILTERING;'
    results = list(session.execute(query, [repo_name]))
    if not results:
        print(f"No commits found for repository '{repo_name}'.")
        return
    counts = {}
    for row in results:
        author = row.author_name or "unknown"
        counts[author] = counts.get(author, 0) + 1
    print(f"\nCommit activity for '{repo_name}' ({len(results)} commit(s) total):")
    for author, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        bar = "#" * count
        print(f"  {author:<25} {bar} ({count})")


# ---------------- Menu ----------------

def print_menu():
    print("\n===== GitHub Archive / Cassandra CRUD Menu =====")
    print("1. Create a commit record")
    print("2. Read a commit record")
    print("3. Update a commit record")
    print("4. Delete a commit record")
    print("5. Feature: Programming language popularity")
    print("6. Feature: A contributor's commit history")
    print("7. Feature: Commit activity visualization for a repo")
    print("8. Exit")


def main():
    create_keyspace_and_tables()
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
