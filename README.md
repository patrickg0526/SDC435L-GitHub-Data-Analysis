# SDC435L Group Project — GitHub Archive Data Analysis

SDC435L
patgon2554

A Python application that integrates multiple NoSQL databases (and finally a relational database) with data from the [GitHub Archive](https://www.gharchive.org/) dataset, built over five weekly project parts: Redis, MongoDB, Cassandra, Neo4j, and SQLite.

**Status:** Individual submission (no group has been assigned/formed yet).

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

### Next Goals

Find or be assigned a project group and coordinate repository access and task division for Parts 3 through 5 (Cassandra, Neo4j, SQLite). Combine the Redis and MongoDB versions of the app behind one shared menu, letting the user pick a backend. Add automated tests for the CRUD operations instead of only manual verification.
