// MongoDB queries of the project (database movielens, collection movies).
// Run with: docker exec -i movielens_mongo mongosh movielens --quiet < mongodb/queries.js

function title(text) { print("\n===== " + text + " ====="); }

// ---------- SIMPLE QUERIES ----------

title("S1 - find + projection: the movie Toy Story");
printjson(db.movies.find(
  { title: "Toy Story" },
  { _id: 0, title: 1, year: 1, genres: 1 }
).toArray());

title("S2 - filters on an array and a number: comedies released in 1995 (first 5)");
printjson(db.movies.find(
  { genres: "Comedy", year: 1995 },
  { _id: 0, title: 1 }
).sort({ title: 1 }).limit(5).toArray());

title("S3 - filter on tags: movies tagged 'pixar'");
printjson(db.movies.find(
  { tags: "pixar" },
  { _id: 0, title: 1, year: 1 }
).toArray());

title("S4 - count: movies without any genre");
print(db.movies.countDocuments({ genres: { $size: 0 } }));

// ---------- ADVANCED QUERIES ----------

title("A1 - $unwind + $group: number of movies and average rating per genre");
printjson(db.movies.aggregate([
  { $unwind: "$genres" },
  { $group: { _id: "$genres", movies: { $sum: 1 }, avg_rating: { $avg: "$stats.rating_avg" } } },
  { $project: { _id: 0, genre: "$_id", movies: 1, avg_rating: { $round: ["$avg_rating", 2] } } },
  { $sort: { movies: -1 } }
]).toArray());

title("A2 - $match + $sort + $limit: top 5 movies with at least 50 ratings");
printjson(db.movies.aggregate([
  { $match: { "stats.rating_count": { $gte: 50 } } },
  { $sort: { "stats.rating_avg": -1, "stats.rating_count": -1 } },
  { $limit: 5 },
  { $project: { _id: 0, title: 1, year: 1, avg: "$stats.rating_avg", ratings: "$stats.rating_count" } }
]).toArray());

title("A3 - $group with a computed key: number of movies per decade");
printjson(db.movies.aggregate([
  { $match: { year: { $ne: null } } },
  { $group: { _id: { $multiply: [{ $floor: { $divide: ["$year", 10] } }, 10] }, movies: { $sum: 1 } } },
  { $sort: { _id: 1 } },
  { $project: { _id: 0, decade: "$_id", movies: 1 } }
]).toArray());

title("A4 - statistics: min, max and average of the movie ratings");
printjson(db.movies.aggregate([
  { $match: { "stats.rating_count": { $gt: 0 } } },
  { $group: {
      _id: null,
      rated_movies: { $sum: 1 },
      best_avg: { $max: "$stats.rating_avg" },
      worst_avg: { $min: "$stats.rating_avg" },
      overall_avg: { $avg: "$stats.rating_avg" },
      most_ratings: { $max: "$stats.rating_count" }
  } },
  { $project: { _id: 0, rated_movies: 1, best_avg: 1, worst_avg: 1,
                overall_avg: { $round: ["$overall_avg", 2] }, most_ratings: 1 } }
]).toArray());

title("A5 - query using an index: explain() of the search by genre");
const plan = db.movies.find({ genres: "Comedy" }).explain("executionStats");
printjson({
  index_used: JSON.stringify(plan.queryPlanner.winningPlan).includes("IXSCAN") ? "IXSCAN (genres_1)" : "COLLSCAN",
  documents_examined: plan.executionStats.totalDocsExamined,
  documents_returned: plan.executionStats.nReturned
});