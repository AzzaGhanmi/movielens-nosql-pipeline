"""Transfer the movies (MongoDB) and the ratings (Cassandra) to Elasticsearch.

Run with Docker Compose:  docker compose up -d --build
Or from the PC:           python src/transfer_to_elasticsearch.py
"""

import os
import sys

from cassandra.cluster import Cluster
from elasticsearch import Elasticsearch, helpers
from pymongo import MongoClient

# Addresses of the databases: Docker Compose service names, or localhost by default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27018")
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
ES_URL = os.getenv("ES_URL", "http://localhost:9200")

MOVIES_INDEX = "movies"
RATINGS_INDEX = "ratings"

# Full-text search on the title, plus an exact copy (keyword) for sorting and aggregations
TEXT_AND_KEYWORD = {"type": "text", "fields": {"keyword": {"type": "keyword"}}}

MOVIES_MAPPING = {
    "properties": {
        "title": TEXT_AND_KEYWORD,
        "year": {"type": "integer"},
        "genres": {"type": "keyword"},
        "tags": TEXT_AND_KEYWORD,
        "imdb_id": {"type": "keyword"},
        "tmdb_id": {"type": "integer"},
        "rating_count": {"type": "integer"},
        "rating_avg": {"type": "float"},
    }
}

# Elasticsearch has no joins: the movie fields are copied into each rating
RATINGS_MAPPING = {
    "properties": {
        "user_id": {"type": "integer"},
        "movie_id": {"type": "integer"},
        "rating": {"type": "float"},
        "rated_at": {"type": "date"},
        "title": TEXT_AND_KEYWORD,
        "genres": {"type": "keyword"},
        "movie_year": {"type": "integer"},
    }
}


# ---------- EXTRACT ----------

def read_movies(mongo):
    """All the documents of the movies collection."""
    return list(mongo["movielens"]["movies"].find())


def read_ratings(session):
    """All the ratings, read page by page from one Cassandra table."""
    session.default_fetch_size = 5000
    query = "SELECT user_id, movie_id, rating, rated_at FROM movielens.ratings_by_user"
    return list(session.execute(query))


# ---------- TRANSFORM ----------

def movie_to_action(movie):
    """MongoDB document -> Elasticsearch bulk action (the MongoDB _id is kept)."""
    return {
        "_index": MOVIES_INDEX,
        "_id": movie["_id"],
        "_source": {
            "title": movie["title"],
            "year": movie["year"],
            "genres": movie["genres"],
            "tags": movie["tags"],
            "imdb_id": movie["links"]["imdb"],
            "tmdb_id": movie["links"]["tmdb"],
            "rating_count": movie["stats"]["rating_count"],
            "rating_avg": movie["stats"]["rating_avg"],
        },
    }


def rating_to_action(row, movies_by_id):
    """Cassandra row + its movie -> Elasticsearch bulk action."""
    movie = movies_by_id.get(row.movie_id, {})
    return {
        "_index": RATINGS_INDEX,
        "_id": f"{row.user_id}_{row.movie_id}",    # one rating per user and movie
        "_source": {
            "user_id": row.user_id,
            "movie_id": row.movie_id,
            "rating": row.rating,
            "rated_at": row.rated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": movie.get("title"),
            "genres": movie.get("genres", []),
            "movie_year": movie.get("year"),
        },
    }


# ---------- LOAD ----------

def create_index(es, name, mapping):
    """(Re)create an index, so the script can be run several times."""
    if es.indices.exists(index=name):
        es.indices.delete(index=name)
    es.indices.create(index=name, mappings=mapping,
                      settings={"number_of_replicas": 0})   # one node: no replica


def main():
    es = Elasticsearch(ES_URL)
    mongo = MongoClient(MONGO_URI)
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect()

    # Extract
    movies = read_movies(mongo)
    ratings = read_ratings(session)
    movies_by_id = {movie["_id"]: movie for movie in movies}

    # Transform + Load (bulk API: thousands of documents per request)
    create_index(es, MOVIES_INDEX, MOVIES_MAPPING)
    helpers.bulk(es, (movie_to_action(m) for m in movies), chunk_size=2000)

    create_index(es, RATINGS_INDEX, RATINGS_MAPPING)
    helpers.bulk(es, (rating_to_action(r, movies_by_id) for r in ratings), chunk_size=5000)

    es.indices.refresh(index=[MOVIES_INDEX, RATINGS_INDEX])

    # Verification: same number of documents on both sides
    checks = [
        ("MongoDB movies   -> ES movies ", len(movies), es.count(index=MOVIES_INDEX)["count"]),
        ("Cassandra ratings -> ES ratings", len(ratings), es.count(index=RATINGS_INDEX)["count"]),
    ]
    print("=== Transfer report ===")
    all_ok = True
    for label, source, target in checks:
        status = "OK" if source == target else "MISMATCH"
        all_ok = all_ok and source == target
        print(f"{label}: {source} -> {target}  {status}")

    cluster.shutdown()
    mongo.close()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()