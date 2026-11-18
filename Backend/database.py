import sqlite3
import os


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "movies.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# MOVIES TABLE
# ============================================================

def create_movies_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            overview TEXT,
            release_date TEXT,
            rating REAL,
            poster_url TEXT,
            backdrop_url TEXT,
            genres TEXT,
            language TEXT,
            popularity REAL,
            vote_count INTEGER,
            adult INTEGER
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# USERS TABLE
# ============================================================

def create_users_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# ADMINS TABLE
# ============================================================

def create_admins_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# WATCHLIST TABLE
# ============================================================

def create_watchlist_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, movie_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# HISTORY TABLE
# ============================================================

def create_history_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, movie_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# TRAILER ACTIVITY TABLE
# ============================================================

def create_trailer_activity_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trailer_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,

            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            watch_duration REAL DEFAULT 0,

            watch_percentage REAL DEFAULT 0,

            interest_level TEXT DEFAULT NULL,

            completed INTEGER DEFAULT 0,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# INSERT MOVIE
# ============================================================

def insert_movie(movie):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        tmdb_id = movie.get(
            "id",
            movie.get("tmdb_id")
        )

        if not tmdb_id:
            return

        # =================================================
        # GENRES
        # =================================================

        genres = movie.get("genres", "")

        if isinstance(genres, list):

            genre_names = []

            for genre in genres:

                if isinstance(genre, dict):

                    name = genre.get("name")

                    if name:
                        genre_names.append(name)

                elif isinstance(genre, str):

                    genre_names.append(genre)

            genres = ", ".join(
                genre_names
            )

        # If genres are still empty, use genre_ids
        if not genres:

            genre_ids = movie.get(
                "genre_ids",
                []
            )

            genre_names = []

            genre_map = {
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

            for genre_id in genre_ids:

                if genre_id in genre_map:

                    genre_names.append(
                        genre_map[genre_id]
                    )

            genres = ", ".join(
                genre_names
            )

        # =================================================
        # INSERT / UPDATE
        # =================================================

        cursor.execute(
            """
            INSERT INTO movies
            (
                tmdb_id,
                title,
                overview,
                release_date,
                rating,
                poster_url,
                backdrop_url,
                genres,
                language,
                popularity,
                vote_count,
                adult
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(tmdb_id)
            DO UPDATE SET

                title = excluded.title,

                overview = excluded.overview,

                release_date =
                    excluded.release_date,

                rating =
                    excluded.rating,

                poster_url =
                    excluded.poster_url,

                backdrop_url =
                    excluded.backdrop_url,

                genres =
                    excluded.genres,

                language =
                    excluded.language,

                popularity =
                    excluded.popularity,

                vote_count =
                    excluded.vote_count,

                adult =
                    excluded.adult
            """,
            (
                tmdb_id,

                movie.get(
                    "title",
                    ""
                ),

                movie.get(
                    "overview",
                    ""
                ),

                movie.get(
                    "release_date",
                    ""
                ),

                movie.get(
                    "vote_average",
                    movie.get(
                        "rating",
                        0
                    )
                ) or 0,

                movie.get(
                    "poster_path",
                    movie.get(
                        "poster_url",
                        ""
                    )
                ),

                movie.get(
                    "backdrop_path",
                    movie.get(
                        "backdrop_url",
                        ""
                    )
                ),

                genres,

                movie.get(
                    "original_language",
                    movie.get(
                        "language",
                        ""
                    )
                ),

                movie.get(
                    "popularity",
                    0
                ) or 0,

                movie.get(
                    "vote_count",
                    0
                ) or 0,

                int(
                    movie.get(
                        "adult",
                        False
                    )
                )
            )
        )

        connection.commit()

    except sqlite3.Error as e:

        connection.rollback()

        print(
            "Movie Insert/Update Error:",
            e
        )

    finally:

        connection.close()

# ============================================================
# FORMAT MOVIE
# ============================================================
# ============================================================
# FORMAT MOVIE
# ============================================================

def format_movie(row):

    movie = dict(row)

    # ========================================================
    # POSTER
    # ========================================================

    poster = movie.get(
        "poster_url"
    )

    if poster:

        if poster.startswith(
            "http"
        ):

            movie["poster_url"] = poster

        else:

            movie["poster_url"] = (
                "https://image.tmdb.org/t/p/w500"
                +
                poster
            )

    else:

        movie["poster_url"] = ""

    # ========================================================
    # BACKDROP
    # ========================================================

    backdrop = movie.get(
        "backdrop_url"
    )

    if backdrop:

        if backdrop.startswith(
            "http"
        ):

            movie["backdrop_url"] = backdrop

        else:

            movie["backdrop_url"] = (
                "https://image.tmdb.org/t/p/original"
                +
                backdrop
            )

    else:

        movie["backdrop_url"] = ""

    # ========================================================
    # OTHER DATA
    # ========================================================

    movie["tmdb_id"] = movie.get(
        "tmdb_id"
    )

    movie["rating"] = (
        movie.get(
            "rating",
            0
        )
        or 0
    )

    movie["genres"] = (
        movie.get(
            "genres",
            ""
        )
        or ""
    )

    return movie


# ============================================================
# GET ALL MOVIES
# ============================================================

def get_all_movies():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        ORDER BY rating DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# TRENDING MOVIES
# ============================================================

def get_trending_movies_db(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE release_date <= DATE('now')
        ORDER BY popularity DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# UPCOMING MOVIES
# ============================================================

# ============================================================
# UPCOMING / NEW RELEASES FROM DATABASE
# ============================================================

def get_upcoming_movies_db(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE release_date >= DATE('now')
        AND poster_url IS NOT NULL
        AND poster_url != ''
        ORDER BY release_date ASC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]

# ============================================================
# TOP RATED MOVIES
# ============================================================

def get_top_rated_movies_db(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        ORDER BY rating DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# SEARCH MOVIES
# ============================================================

def search_movies(search_text):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE title LIKE ?
        ORDER BY popularity DESC
    """, (f"%{search_text}%",))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# MOVIES BY GENRE
# ============================================================

def get_movies_by_genre(genre):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE genres LIKE ?
        ORDER BY popularity DESC
    """, (f"%{genre}%",))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# MOVIES BY LANGUAGE
# ============================================================

def get_movies_by_language(language):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE language = ?
        ORDER BY popularity DESC
    """, (language,))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# MOVIES BY GENRE WITH LIMIT
# ============================================================

def get_movies_by_genre_limit(genre, limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM movies
        WHERE genres LIKE ?
        ORDER BY popularity DESC
        LIMIT ?
    """, (
        f"%{genre}%",
        limit
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        format_movie(row)
        for row in rows
    ]


# ============================================================
# USER WATCHLIST
# ============================================================

def get_user_watchlist(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            w.movie_id,
            w.created_at,
            m.title,
            m.genres,
            m.rating
        FROM watchlist w

        LEFT JOIN movies m
            ON w.movie_id = m.tmdb_id

        WHERE w.user_id = ?

        ORDER BY w.created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# USER HISTORY
# ============================================================

def get_user_history(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            h.movie_id,
            h.watched_at,
            m.title,
            m.genres,
            m.rating
        FROM history h

        LEFT JOIN movies m
            ON h.movie_id = m.tmdb_id

        WHERE h.user_id = ?

        ORDER BY h.watched_at DESC
    """, (user_id,))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# USER TRAILER ACTIVITY
# ============================================================

def get_user_trailer_activity(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            t.movie_id,
            t.started_at,
            t.watch_duration,
            t.watch_percentage,
            t.interest_level,
            t.completed,
            m.title,
            m.genres,
            m.rating

        FROM trailer_activity t

        LEFT JOIN movies m
            ON t.movie_id = m.tmdb_id

        WHERE t.user_id = ?

        ORDER BY t.started_at DESC
    """, (user_id,))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# CREATE DATABASE
# ============================================================

def initialize_database():

    create_movies_table()
    create_users_table()
    create_admins_table()
    create_watchlist_table()
    create_history_table()
    create_trailer_activity_table()

    print("=" * 60)
    print("DATABASE INITIALIZED")
    print("=" * 60)


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print("Movies table checked!")
    print("Users table checked!")
    print("Admins table checked!")
    print("Watchlist table checked!")
    print("History table checked!")
    print("Trailer activity table checked!")