import time
import requests

from config import TMDB_API_KEY, TMDB_BASE_URL
from database import create_movies_table, insert_movie

DISCOVER_YEARS = [
    2026,
    2025,
    2024,
    2023,
    2022,
    2021,
    2020,
    2019,
    2018,
    2017,
    2016,
    2015,
    2014,
    2013,
    2012,
    2011,
    2010
]

# Genre ID -> Genre Name mapping
GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}


def fetch_movies(year, page):

    url = f"{TMDB_BASE_URL}/discover/movie"

    params = {
    "api_key": TMDB_API_KEY,
    "primary_release_year": year,
    "sort_by": "popularity.desc",
    "page": page,
    "include_adult": False,
    "vote_count.gte": 50
}

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(3):

        try:

            print(f"Downloading {year} - Page {page}")

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            return response.json()["results"]

        except requests.exceptions.RequestException as e:

            print(f"Attempt {attempt + 1} failed ({year} Page {page})")
            print(e)

            if attempt < 2:
                print("Retrying in 2 seconds...")
                time.sleep(2)

    print(f"Skipping {year} Page {page}")
    return []


if __name__ == "__main__":

    create_movies_table()

    total_movies = 0

    for year in DISCOVER_YEARS:

        print(f"\n========== {year} ==========\n")

        for page in range(1, 11):

            movies = fetch_movies(year, page)

            for movie in movies:

                genre_names = []

                for genre_id in movie.get("genre_ids", []):

                    if genre_id in GENRES:
                        genre_names.append(GENRES[genre_id])

                movie["genres"] = ", ".join(genre_names)

                insert_movie(movie)
                total_movies += 1

            time.sleep(1)

    print("\n===================================")
    print(f"Processed approximately {total_movies} movies.")
    print("===================================")