// Indexes for the "movies" collection.
// Run with: docker exec -i movielens_mongo mongosh movielens --quiet < mongodb/create_indexes.js

// Q2: search movies by genre, by release year and by tag
db.movies.createIndex({ genres: 1 });
db.movies.createIndex({ year: 1 });
db.movies.createIndex({ tags: 1 });

// Show the result
printjson(db.movies.getIndexes().map(index => index.name));