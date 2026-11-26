"""Clean the MovieLens CSV files and build movies.json for MongoDB.

Run from the project root:  python src/data_cleaning.py
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

# Path of the data folder: one level above src/
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "movies.json"                         

# Pattern for a year in parentheses at the end of a title, e.g. "(1995)"
YEAR_PATTERN = re.compile(r"\s*\((\d{4})\)\s*$")

# Articles that MovieLens moves to the end of titles ("Matrix, The")
ARTICLES = ["The", "A", "An", "Les", "Le", "La", "L'", "Il", "El",
            "Los", "Las", "Der", "Die", "Das"]
ARTICLE_PATTERN = re.compile(r"^(.*), (" + "|".join(re.escape(a) for a in ARTICLES) + r")$")

# Value used by MovieLens when a movie has no genre
NO_GENRE = "(no genres listed)"


# ---------- EXTRACT ----------

def read_csv(file_name):
    """Read a CSV file from the data folder as a list of dictionaries."""
    with open(DATA_DIR / file_name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------- TRANSFORM ----------

def split_title_year(raw_title):
    """'Toy Story (1995)' -> ('Toy Story', 1995). The year is None if missing."""
    match = YEAR_PATTERN.search(raw_title)
    if match:
        year = int(match.group(1))
        title = raw_title[:match.start()].strip()
        return title, year
    return raw_title.strip(), None


def move_article(title):
    """'Matrix, The' -> 'The Matrix'. Titles without a final article are unchanged."""
    match = ARTICLE_PATTERN.match(title)
    if not match:
        return title
    article = match.group(2)
    separator = "" if article.endswith("'") else " "           # "L'Atalante", not "L' Atalante"
    return article + separator + match.group(1)


def clean_title(raw_title):
    """Full title cleaning: split the year, then move the article."""
    title, year = split_title_year(raw_title)
    return move_article(title), year


def split_genres(raw_genres):
    """'Adventure|Animation' -> ['Adventure', 'Animation']; '(no genres listed)' -> []."""
    if raw_genres == NO_GENRE:
        return []
    return raw_genres.split("|")


def group_tags(tag_rows):
    """One row per tag -> {movieId: [unique lowercase tags]}."""
    tags_by_movie = defaultdict(list)
    for row in tag_rows:
        tag = row["tag"].strip().lower()
        if tag and tag not in tags_by_movie[row["movieId"]]:
            tags_by_movie[row["movieId"]].append(tag)
    return tags_by_movie


def build_links(link_rows):
    """One row per movie -> {movieId: {"imdb": "tt0114709", "tmdb": 862}}."""
    links_by_movie = {}
    for row in link_rows:
        imdb = "tt" + row["imdbId"].zfill(7) if row["imdbId"] else None
        tmdb = int(row["tmdbId"]) if row["tmdbId"] else None
        links_by_movie[row["movieId"]] = {"imdb": imdb, "tmdb": tmdb}
    return links_by_movie


def compute_rating_stats(rating_rows):
    """One row per rating -> {movieId: {"rating_count": 215, "rating_avg": 3.92}}."""
    count = defaultdict(int)
    total = defaultdict(float)
    for row in rating_rows:
        count[row["movieId"]] += 1
        total[row["movieId"]] += float(row["rating"])
    return {movie_id: {"rating_count": count[movie_id],
                       "rating_avg": round(total[movie_id] / count[movie_id], 2)}
            for movie_id in count}


def build_movie_documents(movies, tags_by_movie, links_by_movie, stats_by_movie):   
    """Assemble one MongoDB document per movie from the four sources."""
    no_stats = {"rating_count": 0, "rating_avg": None}
    no_links = {"imdb": None, "tmdb": None}
    documents = []
    for movie in movies:
        movie_id = movie["movieId"]
        title, year = clean_title(movie["title"])
        documents.append({
            "_id": int(movie_id),
            "title": title,
            "year": year,
            "genres": split_genres(movie["genres"]),
            "tags": tags_by_movie.get(movie_id, []),
            "links": links_by_movie.get(movie_id, no_links),
            "stats": stats_by_movie.get(movie_id, no_stats),
        })
    return documents


# ---------- LOAD (write the file that MongoDB will import) ----------

def write_json(documents, path):                               
    """Write the documents as a JSON array, keeping accents readable."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)


def main():                                                    
    # Extract
    movies = read_csv("movies.csv")
    tag_rows = read_csv("tags.csv")
    link_rows = read_csv("links.csv")
    rating_rows = read_csv("ratings.csv")

    # Transform
    documents = build_movie_documents(
        movies,
        group_tags(tag_rows),
        build_links(link_rows),
        compute_rating_stats(rating_rows),
    )

    # Load
    write_json(documents, OUTPUT_FILE)

    # Quality report
    print("=== Data cleaning report ===")
    print("Movies written:          ", len(documents))
    print("Movies without a year:   ", sum(1 for d in documents if d["year"] is None))
    print("Movies without a genre:  ", sum(1 for d in documents if not d["genres"]))
    print("Movies with tags:        ", sum(1 for d in documents if d["tags"]))
    print("Movies without a rating: ", sum(1 for d in documents if d["stats"]["rating_count"] == 0))
    print("Output file:             ", OUTPUT_FILE)
    print("Example document:")
    print(json.dumps(documents[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":                                     
    main()