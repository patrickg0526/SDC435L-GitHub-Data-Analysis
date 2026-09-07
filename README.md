# SDC435L Group Project — GitHub Archive Data Analysis

SDC435L
patgon2554

A Python application that integrates multiple NoSQL databases (and finally a relational database) with data from the [GitHub Archive](https://www.gharchive.org/) dataset, built over five weekly project parts: Redis, MongoDB, Cassandra, Neo4j, and SQLite.

**Status:** Individual submission for Part 1 (no group has been assigned/formed yet).

## Part 1: Redis Integration

`githubRedisApp.py` imports a sample of GitHub Archive commit and language data into a local Redis key-value database, performs CRUD operations on commit records, and includes three analysis features.

### Dependencies

- Python 3.x
- [redis-py](https://pypi.org/project/redis/) (`pip3 install redis`)
- A running local Redis server (`redis-server`)

### Technology Requirements

- Linux environment (developed/tested on Ubuntu via WSL2) with a Redis server installed and running on `127.0.0.1:6379`
- The `GitHubArchive-Dataset` folder (containing `Commits.json` and `Languages.json`) present alongside `githubRedisApp.py`

### Setup / Running the Application

```bash
pip3 install redis
redis-server &          # if not already running
python3 githubRedisApp.py
```

On startup, the app imports a sample of records (2,000 commits, language stats from 5,000 repositories) into Redis, then presents a menu.

### Current Features

- **CRUD operations on commit records** — Create, Read, Update, and Delete individual commit records stored as Redis hashes (`commit:<hash>`), indexed by repository (`repo:<name>`) and by author email (`author:<email>`) for fast lookup.
- **Feature 1 — Programming language popularity:** aggregates total bytes per language (Redis sorted set) across sampled repositories and displays the top N languages.
- **Feature 2 — A contributor's commit history:** given an author's email, lists all of that author's commits found in the imported sample.
- **Feature 3 — Commit activity visualization:** given a repository name, prints an ASCII bar chart of commit counts per author for that repository.

### Next Goals

- Find/join a project group and coordinate repository access and task division for Parts 2-5.
- Expand the imported sample size and add pagination for large result sets.
- Consider adding a real chart (matplotlib) for Feature 3 instead of an ASCII bar chart.
