-- Cassandra queries of the project (keyspace movielens).
-- Each query gives the partition key: Cassandra opens one partition only.
-- Run with: docker exec -it movielens_cassandra cqlsh -k movielens   (then paste a query)

-- ---------- SIMPLE QUERIES ----------

-- S5: last 5 ratings of user 1 (partition user_id, sorted by rated_at DESC)
SELECT rated_at, movie_id, rating FROM ratings_by_user WHERE user_id = 1 LIMIT 5;

-- S6: last 5 ratings of the movie 356 (Forrest Gump)
SELECT rated_at, user_id, rating FROM ratings_by_movie WHERE movie_id = 356 LIMIT 5;

-- S7: last 5 ratings of August 2000 (composite partition key year + month)
SELECT rated_at, user_id, movie_id, rating FROM ratings_by_month WHERE year = 2000 AND month = 8 LIMIT 5;

-- ---------- ADVANCED QUERIES ----------

-- A6: statistics of one movie: number, average, min and max of its ratings
SELECT COUNT(*) AS ratings, AVG(rating) AS avg_rating, MIN(rating) AS min_rating, MAX(rating) AS max_rating
  FROM ratings_by_movie WHERE movie_id = 356;

-- A7: range on the clustering column: ratings given by user 414 during the year 2000
SELECT COUNT(*) AS ratings_in_2000 FROM ratings_by_user
  WHERE user_id = 414 AND rated_at >= '2000-01-01' AND rated_at < '2001-01-01';

-- A8: statistics of the busiest month (biggest partition of ratings_by_month)
SELECT COUNT(*) AS ratings, AVG(rating) AS avg_rating FROM ratings_by_month WHERE year = 2017 AND month = 5;

-- Demonstration: a query WITHOUT the partition key is refused by Cassandra
SELECT * FROM ratings_by_user WHERE movie_id = 356;