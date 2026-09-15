# SDC435L Group Project — GitHub Archive Data Analysis

SDC435L
patgon2554

A Python application that integrates multiple NoSQL databases (and finally a relational database) with data from the [GitHub Archive](https://www.gharchive.org/) dataset, built over five weekly project parts: Redis, MongoDB, Cassandra, Neo4j, and SQLite.

**Status:** Individual submission.

## Part 1: Redis Integration

`githubRedisApp.py` imports a sample of GitHub Archive commit and language data into a local Redis key-value database, performs CRUD operations on commit records, and includes three analysis features.

### Dependencies

Python 3.x. redis-py, installed via pip3 install redis. A running local Redis server (redis-server).

### Technology Requirements

Linux environment (developed/tested on Ubuntu via WSL2) with a Redis server installed and running on 127.0.0.1:6379. The GitHubArchive-Dataset folder (containing Commits.json and Languages.json) present alongside githubRedisApp.py.

### Setup / Running

pip3 install redis, then redis-server (if not already running), then python3 githubRedisApp.py. On startup, the app imports a sample of records (2,000 commits, language stats from 5,000 repositories) into Redis, then presents a menu.

### Current Features

CRUD operations on commit records, stored as Redis hashes (commit:hash), indexed by repository and by author email for fast lookup. Feature 1, programming language popularity: aggregates total bytes per language (Redis sorted set) across sampled repositories and displays the top N languages. Feature 2, a contributor's commit history: given an author's email, lists all of that author's commits found in the imported sample. Feature 3, commit activity visualization: given a repository name, prints an ASCII bar chart of commit counts per author for that repository.

## Part 2: MongoDB Integration

`githubMongoApp.py` imports the same sample of GitHub Archive commit and language data into a local MongoDB database, performs CRUD operations on commit documents, and includes the same three analysis features rebuilt for MongoDB.

### Dependencies

Python 3.x. pymongo, installed via pip3 install pymongo. A running local MongoDB server (mongod) on 127.0.0.1:27017.

### Setup / Running

pip3 install pymongo, then python3 githubMongoApp.py. On startup, the app imports a sample of records (2,000 commits, language stats from 5,000 repositories) into a GitHubArchive database (Commits and Languages collections), then presents a menu.

### Current Features

CRUD operations on commit documents in the Commits collection, indexed by commit_hash, repo_name, and author_email. Feature 1, programming language popularity: aggregates total bytes per language into a Languages collection and displays the top N languages. Feature 2, a contributor's commit history: given an author's email, lists all of that author's commits found in the imported sample. Feature 3, commit activity visualization: given a repository name, prints an ASCII bar chart of commit counts per author for that repository.

## Part 3: Cassandra Integration

`githubCassandraApp.py` imports the same sample of GitHub Archive commit and language data into a local Cassandra column-family database, performs CRUD operations on commit records, and includes the same three analysis features rebuilt for Cassandra.

### Dependencies

Python 3.x. cassandra-driver (python3-cassandra), installed via apt or pip3 install cassandra-driver. A running local Cassandra cluster on 127.0.0.1:9042.

### Technology Requirements

Linux environment (developed/tested on Ubuntu via WSL2) with Cassandra 4.1 installed and running. The GitHubArchive-Dataset folder (containing Commits.json and Languages.json) present alongside githubCassandraApp.py.

### Setup / Running

Install cassandra-driver, make sure the Cassandra service is running, then python3 githubCassandraApp.py. On startup, the app creates a GitHubArchive keyspace with Commits and Languages tables, imports a sample of records (2,000 commits, language stats from 5,000 repositories), then presents a menu.

### Current Features

CRUD operations on commit records in the Commits table, keyed by commit_hash, with author-based lookups using ALLOW FILTERING. Feature 1, programming language popularity: aggregates total bytes per language into a Languages table and displays the top N languages. Feature 2, a contributor's commit history: given an author's email, lists all of that author's commits found in the imported sample. Feature 3, commit activity visualization: given a repository name, prints an ASCII bar chart of commit counts per author for that repository. The top languages by total bytes match the Redis and MongoDB versions exactly, confirming consistent data handling across all three databases.

### Next Goals

Continue building out Parts 4 and 5 (Neo4j, SQLite). Combine the Redis, MongoDB, and Cassandra versions of the app behind one shared menu, letting the user pick a backend. Add automated tests for the CRUD operations instead of only manual verification.
