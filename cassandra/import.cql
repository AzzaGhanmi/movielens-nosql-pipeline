-- Load the prepared CSV files (src/prepare_ratings.py) into the tables.
-- Run with: docker exec movielens_cassandra cqlsh -f /cassandra/import.cql
-- The data/ folder is mounted read-only in the container as /data/import.

COPY movielens.ratings_by_user (user_id, rated_at, movie_id, rating)
  FROM '/data/import/ratings_by_user.csv' WITH HEADER = TRUE;

COPY movielens.ratings_by_movie (movie_id, rated_at, user_id, rating)
  FROM '/data/import/ratings_by_movie.csv' WITH HEADER = TRUE;

COPY movielens.ratings_by_month (year, month, rated_at, user_id, movie_id, rating)
  FROM '/data/import/ratings_by_month.csv' WITH HEADER = TRUE;