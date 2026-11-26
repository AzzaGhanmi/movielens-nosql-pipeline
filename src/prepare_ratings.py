"""Prepare the MovieLens ratings for Cassandra: one CSV file per table.

Run from the project root:  python src/prepare_ratings.py
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

# Path of the data folder: one level above src/
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# One output file per Cassandra table, with its columns in COPY order
OUTPUT_FILES = {
    "ratings_by_user.csv":  ["user_id", "rated_at", "movie_id", "rating"],
    "ratings_by_movie.csv": ["movie_id", "rated_at", "user_id", "rating"],
    "ratings_by_month.csv": ["year", "month", "rated_at", "user_id", "movie_id", "rating"],
}


# ---------- EXTRACT ----------

def read_ratings():
    """Read ratings.csv as a list of dictionaries."""
    with open(DATA_DIR / "ratings.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------- TRANSFORM ----------

def to_datetime(unix_seconds):
    """964982703 -> datetime 2000-07-30 18:45:03 UTC."""
    return datetime.fromtimestamp(int(unix_seconds), tz=timezone.utc)


def build_rows(raw_ratings):
    """Rename the columns, convert the types and add the date parts."""
    rows = []
    for raw in raw_ratings:
        rated_at = to_datetime(raw["timestamp"])
        rows.append({
            "user_id": int(raw["userId"]),
            "movie_id": int(raw["movieId"]),
            "rating": float(raw["rating"]),
            "rated_at": rated_at.strftime("%Y-%m-%d %H:%M:%S+0000"),  # format read by cqlsh COPY
            "year": rated_at.year,
            "month": rated_at.month,
        })
    return rows


# ---------- LOAD (write the files that cqlsh COPY will import) ----------

def write_csv(rows, file_name, columns):
    """Write only the given columns, in the given order, with a header line."""
    with open(DATA_DIR / file_name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    raw_ratings = read_ratings()
    rows = build_rows(raw_ratings)
    for file_name, columns in OUTPUT_FILES.items():
        write_csv(rows, file_name, columns)

    # Quality report
    months = {(r["year"], r["month"]) for r in rows}
    print("=== Ratings preparation report ===")
    print("Ratings read:     ", len(raw_ratings))
    print("Ratings written:  ", len(rows), "per file")
    print("Users:            ", len({r["user_id"] for r in rows}))
    print("Movies rated:     ", len({r["movie_id"] for r in rows}))
    print("Months (partitions of ratings_by_month):", len(months))
    print("First rating:     ", min(r["rated_at"] for r in rows))
    print("Last rating:      ", max(r["rated_at"] for r in rows))
    for file_name in OUTPUT_FILES:
        print("Output file:      ", DATA_DIR / file_name)


if __name__ == "__main__":
    main()