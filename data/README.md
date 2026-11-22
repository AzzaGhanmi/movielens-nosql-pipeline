# Dataset: MovieLens (ml-latest-small)

This project uses the **MovieLens ml-latest-small** dataset, created by GroupLens Research (University of Minnesota).

- 9,742 movies
- 100,836 ratings (0.5 to 5 stars) from 610 users, between 1996 and 2018
- 3,683 tags

The data files are **not included** in this repository (see the license below).

## How to get the data

1. Download `ml-latest-small.zip` from https://grouplens.org/datasets/movielens/
2. Unzip it and copy these 4 files into this `data/` folder:

| File | Content |
|------|---------|
| `movies.csv` | movieId, title, genres |
| `ratings.csv` | userId, movieId, rating, timestamp |
| `tags.csv` | userId, movieId, tag, timestamp |
| `links.csv` | movieId, imdbId, tmdbId |

## License and citation

The dataset is used for educational, non-commercial purposes, following the GroupLens license.

> F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context.
> ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872