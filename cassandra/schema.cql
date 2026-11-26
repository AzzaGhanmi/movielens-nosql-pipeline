-- Cassandra schema of the MovieLens project.
-- Run with: docker exec movielens_cassandra cqlsh -f /cassandra/schema.cql

-- Keyspace: one node only, so one copy of each row
CREATE KEYSPACE IF NOT EXISTS movielens
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE movielens;

-- Q1: ratings of a user, most recent first
-- movie_id keeps rows unique when a user rates several movies in the same second
CREATE TABLE IF NOT EXISTS ratings_by_user (
  user_id  int,
  rated_at timestamp,
  movie_id int,
  rating   float,
  PRIMARY KEY ((user_id), rated_at, movie_id)
) WITH CLUSTERING ORDER BY (rated_at DESC, movie_id ASC);

-- Q2: ratings of a movie, most recent first
CREATE TABLE IF NOT EXISTS ratings_by_movie (
  movie_id int,
  rated_at timestamp,
  user_id  int,
  rating   float,
  PRIMARY KEY ((movie_id), rated_at, user_id)
) WITH CLUSTERING ORDER BY (rated_at DESC, user_id ASC);

-- Q3: ratings of a month, most recent first
-- (year, month) instead of year alone: biggest partition 2,397 rows instead of 10,061
CREATE TABLE IF NOT EXISTS ratings_by_month (
  year     int,
  month    int,
  rated_at timestamp,
  user_id  int,
  movie_id int,
  rating   float,
  PRIMARY KEY ((year, month), rated_at, user_id, movie_id)
) WITH CLUSTERING ORDER BY (rated_at DESC, user_id ASC, movie_id ASC);