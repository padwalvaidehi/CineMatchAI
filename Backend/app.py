from config import TMDB_API_KEY, TMDB_BASE_URL
from flask import Flask, render_template, request, redirect, url_for, session, flash

import requests

tmdb_session = requests.Session()

tmdb_session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Connection": "keep-alive"
})

from datetime import datetime
import random
import time
import sqlite3
from admin import admin_bp

from babel import Locale

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import (
    DATABASE_NAME,
    get_all_movies,
    search_movies,
    get_movies_by_genre,
    get_movies_by_language,
    get_trending_movies_db,
    get_upcoming_movies_db,
    get_top_rated_movies_db,
    get_movies_by_genre_limit,
    insert_movie
)


# ============================================================
# GENRES
# ============================================================

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


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "cinematchai-secret-key"


# ============================================================
# AI RECOMMENDATION DATA
# ============================================================

def get_user_activity(user_id):

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # WATCHLIST
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT movie_id
            FROM watchlist
            WHERE user_id = ?
            """,
            (user_id,)
        )

        watchlist = [
            row["movie_id"]
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # WATCH HISTORY
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT movie_id
            FROM history
            WHERE user_id = ?
            """,
            (user_id,)
        )

        history = [
            row["movie_id"]
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # TRAILER ACTIVITY
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                movie_id,
                watch_percentage,
                interest_level
            FROM trailer_activity
            WHERE user_id = ?
            ORDER BY watch_percentage DESC
            """,
            (user_id,)
        )

        trailer_activity = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return {
            "watchlist": watchlist,
            "history": history,
            "trailer_activity": trailer_activity
        }

    except sqlite3.Error as e:

        print(
            "AI Activity Fetch Error:",
            e
        )

        return {
            "watchlist": [],
            "history": [],
            "trailer_activity": []
        }

    finally:

        connection.close()


# ============================================================
# GET LANGUAGES USER HAS ENGAGED WITH
# ============================================================

def get_engaged_languages(user_id):

    activity = get_user_activity(
        user_id
    )

    # =====================================================
    # GET ALL MOVIES USER ENGAGED WITH
    # =====================================================

    watchlist_ids = set(
        activity.get("watchlist", [])
    )

    history_ids = set(
        activity.get("history", [])
    )

    trailer_ids = {
        item["movie_id"]
        for item in activity.get(
            "trailer_activity",
            []
        )
        if item.get("movie_id")
    }

    engaged_movie_ids = (
        watchlist_ids
        |
        history_ids
        |
        trailer_ids
    )

    # =====================================================
    # FIND LANGUAGES
    # =====================================================

    engaged_languages = set()

    for movie_id in engaged_movie_ids:

        try:

            movie = get_movie_details(
                movie_id
            )

            if not movie:
                continue

            language = movie.get(
                "original_language"
            )

            if language:
                engaged_languages.add(
                    language
                )

        except Exception as e:

            print(
                "Language detection error:",
                movie_id,
                e
            )

    print("=" * 60)

    print(
        "ENGAGED LANGUAGES"
    )

    print(
        "User:",
        user_id
    )

    print(
        "Movie IDs:",
        engaged_movie_ids
    )

    print(
        "Languages:",
        engaged_languages
    )

    print("=" * 60)

    return engaged_languages


# ============================================================
# LANGUAGE DISPLAY INFORMATION
# ============================================================

LANGUAGE_INFO = {

    "hi": {
        "name": "Bollywood",
        "flag": "🇮🇳"
    },

    "en": {
        "name": "Hollywood",
        "flag": "🇺🇸"
    },

    "ko": {
        "name": "Korean",
        "flag": "🇰🇷"
    },

    "ja": {
        "name": "Anime",
        "flag": "🇯🇵"
    },

    "th": {
        "name": "Thai",
        "flag": "🇹🇭"
    },

    "zh": {
        "name": "Chinese",
        "flag": "🇨🇳"
    },

    "es": {
        "name": "Spanish",
        "flag": "🇪🇸"
    },

    "fr": {
        "name": "French",
        "flag": "🇫🇷"
    },

    "de": {
        "name": "German",
        "flag": "🇩🇪"
    },

    "it": {
        "name": "Italian",
        "flag": "🇮🇹"
    },

    "ru": {
        "name": "Russian",
        "flag": "🇷🇺"
    }
}


# ============================================================
# PERSONALIZED MOOD + LANGUAGE RECOMMENDATIONS
# ============================================================

def get_personalized_mood_movies(
    user_id,
    mood,
    refresh_seed=None
):

    # --------------------------------------------------------
    # REFRESH SEED
    # --------------------------------------------------------

    if refresh_seed is None:

        refresh_seed = random.randint(
            1,
            999999999
        )

    random.seed(
        refresh_seed
    )

    # --------------------------------------------------------
    # USER ACTIVITY
    # --------------------------------------------------------

    activity = get_user_activity(
        user_id
    )

    watchlist_ids = set(
        activity["watchlist"]
    )

    history_ids = set(
        activity["history"]
    )

    trailer_ids = {
        item["movie_id"]
        for item in activity["trailer_activity"]
    }

    interacted_ids = (
        watchlist_ids
        |
        history_ids
        |
        trailer_ids
    )

    # --------------------------------------------------------
    # ENGAGED LANGUAGES
    # --------------------------------------------------------

    engaged_languages = get_engaged_languages(
        user_id
    )

    print("=" * 60)

    print(
        "PERSONALIZED MOOD RECOMMENDATIONS"
    )

    print(
        "Mood:",
        mood
    )

    print(
        "Languages:",
        engaged_languages
    )

    print(
        "Refresh seed:",
        refresh_seed
    )

    print("=" * 60)

    # --------------------------------------------------------
    # MOOD → GENRES
    # --------------------------------------------------------

    mood_genres = {

        "cozy": [
            "Comedy",
            "Romance",
            "Family"
        ],

        "emotional": [
            "Drama",
            "Romance"
        ],

        "adrenaline": [
            "Action",
            "Thriller"
        ],

        "mystery": [
            "Mystery",
            "Thriller",
            "Crime"
        ],

        "horror": [
            "Horror",
            "Mystery",
            "Thriller"
        ],

        "fantasy": [
            "Fantasy",
            "Adventure"
        ],

        "romance": [
            "Romance",
            "Drama",
            "Comedy"
        ],

        "mind": [
            "Mystery",
            "Science Fiction",
            "Thriller"
        ],

        "funny": [
            "Comedy"
        ],

        "explore": [
            "Adventure",
            "Fantasy",
            "Science Fiction"
        ]
    }

    selected_genres = mood_genres.get(
        mood,
        ["Drama"]
    )

    # --------------------------------------------------------
    # CONVERT GENRE NAMES → TMDB GENRE IDS
    # --------------------------------------------------------

    genre_ids = []

    for genre_id, genre_name in GENRES.items():

        if genre_name in selected_genres:

            genre_ids.append(
                genre_id
            )

    print(
        "Selected genres:",
        selected_genres
    )

    print(
        "Genre IDs:",
        genre_ids
    )

    # --------------------------------------------------------
    # DETERMINE LANGUAGE BALANCE
    # --------------------------------------------------------

    if (
        "hi" in engaged_languages
        and
        "en" in engaged_languages
    ):

        target_languages = {
            "hi": 15,
            "en": 15
        }

    elif "hi" in engaged_languages:

        target_languages = {
            "hi": 30
        }

    elif "en" in engaged_languages:

        target_languages = {
            "en": 30
        }

    else:

        target_languages = {
            "en": 30
        }

    print(
        "Target language balance:",
        target_languages
    )

    # --------------------------------------------------------
    # HELPER FUNCTION
    # --------------------------------------------------------

    def collect_language_movies(
        language,
        target_count
    ):

        collected = {}

        # ----------------------------------------------------
        # LEVEL 1
        # Exact mood genres + selected language
        # ----------------------------------------------------

        pages = list(
            range(1, 11)
        )

        random.shuffle(
            pages
        )

        for page in pages:

            if len(collected) >= target_count:
                break

            try:

                movies = discover_movies(
                    genres=genre_ids,
                    language=language,
                    page=page
                )

                random.shuffle(
                    movies
                )

                for movie in movies:

                    movie_id = movie.get(
                        "id",
                        movie.get("tmdb_id")
                    )

                    if not movie_id:
                        continue

                    if movie_id in interacted_ids:
                        continue

                    if not movie.get(
                        "poster_url"
                    ):
                        continue

                    movie[
                        "recommendation_language"
                    ] = language

                    collected[
                        movie_id
                    ] = movie

                    if len(collected) >= target_count:
                        break

            except Exception as e:

                print(
                    f"{language} mood search error:",
                    e
                )

        # ----------------------------------------------------
        # LEVEL 2
        # Relax genre restriction
        # ----------------------------------------------------

        if len(collected) < target_count:

            print(
                f"Not enough {language} mood movies."
                f" Found {len(collected)}."
                f" Expanding {language} search."
            )

            pages = list(
                range(1, 11)
            )

            random.shuffle(
                pages
            )

            for page in pages:

                if len(collected) >= target_count:
                    break

                try:

                    movies = discover_movies(
                        genres=None,
                        language=language,
                        page=page
                    )

                    random.shuffle(
                        movies
                    )

                    for movie in movies:

                        movie_id = movie.get(
                            "id",
                            movie.get("tmdb_id")
                        )

                        if not movie_id:
                            continue

                        if movie_id in interacted_ids:
                            continue

                        if movie_id in collected:
                            continue

                        if not movie.get(
                            "poster_url"
                        ):
                            continue

                        movie[
                            "recommendation_language"
                        ] = language

                        collected[
                            movie_id
                        ] = movie

                        if len(collected) >= target_count:
                            break

                except Exception as e:

                    print(
                        f"{language} fallback error:",
                        e
                    )

        # ----------------------------------------------------
        # RETURN RANDOMIZED MOVIES
        # ----------------------------------------------------

        movies = list(
            collected.values()
        )

        random.shuffle(
            movies
        )

        return movies[:target_count]

    # --------------------------------------------------------
    # COLLECT MOVIES BY LANGUAGE
    # --------------------------------------------------------

    hindi_movies = []
    english_movies = []

    if "hi" in target_languages:

        hindi_movies = collect_language_movies(
            "hi",
            target_languages["hi"]
        )

    if "en" in target_languages:

        english_movies = collect_language_movies(
            "en",
            target_languages["en"]
        )

    print(
        "Hindi movies collected:",
        len(hindi_movies)
    )

    print(
        "English movies collected:",
        len(english_movies)
    )

    # --------------------------------------------------------
    # COMBINE LANGUAGE RESULTS
    # --------------------------------------------------------

    final_movies = []

    final_movies.extend(
        hindi_movies
    )

    final_movies.extend(
        english_movies
    )

    # --------------------------------------------------------
    # MISSING HINDI / ENGLISH
    # --------------------------------------------------------

    if "hi" in target_languages:

        missing_hindi = (
            target_languages["hi"]
            -
            len(hindi_movies)
        )

    else:

        missing_hindi = 0

    if "en" in target_languages:

        missing_english = (
            target_languages["en"]
            -
            len(english_movies)
        )

    else:

        missing_english = 0

    # --------------------------------------------------------
    # EXTRA HINDI FILL
    # --------------------------------------------------------

    if missing_hindi > 0:

        print(
            "Missing Hindi movies:",
            missing_hindi
        )

        extra_hindi = collect_language_movies(
            "hi",
            missing_hindi + 15
        )

        existing_ids = {
            movie.get(
                "id",
                movie.get("tmdb_id")
            )
            for movie in final_movies
        }

        for movie in extra_hindi:

            movie_id = movie.get(
                "id",
                movie.get("tmdb_id")
            )

            if movie_id in existing_ids:
                continue

            final_movies.append(
                movie
            )

            existing_ids.add(
                movie_id
            )

            missing_hindi -= 1

            if missing_hindi <= 0:
                break

    # --------------------------------------------------------
    # EXTRA ENGLISH FILL
    # --------------------------------------------------------

    if missing_english > 0:

        print(
            "Missing English movies:",
            missing_english
        )

        extra_english = collect_language_movies(
            "en",
            missing_english + 15
        )

        existing_ids = {
            movie.get(
                "id",
                movie.get("tmdb_id")
            )
            for movie in final_movies
        }

        for movie in extra_english:

            movie_id = movie.get(
                "id",
                movie.get("tmdb_id")
            )

            if movie_id in existing_ids:
                continue

            final_movies.append(
                movie
            )

            existing_ids.add(
                movie_id
            )

            missing_english -= 1

            if missing_english <= 0:
                break

    # --------------------------------------------------------
    # FINAL SAFETY FILL
    # --------------------------------------------------------

    if len(final_movies) < 30:

        print(
            "Still need",
            30 - len(final_movies),
            "movies."
        )

        existing_ids = {
            movie.get(
                "id",
                movie.get("tmdb_id")
            )
            for movie in final_movies
        }

        if "hi" in engaged_languages:

            extra_movies = collect_language_movies(
                "hi",
                30
            )

            for movie in extra_movies:

                movie_id = movie.get(
                    "id",
                    movie.get("tmdb_id")
                )

                if movie_id in existing_ids:
                    continue

                final_movies.append(
                    movie
                )

                existing_ids.add(
                    movie_id
                )

                if len(final_movies) >= 30:
                    break

        if (
            len(final_movies) < 30
            and
            "en" in engaged_languages
        ):

            extra_movies = collect_language_movies(
                "en",
                30
            )

            for movie in extra_movies:

                movie_id = movie.get(
                    "id",
                    movie.get("tmdb_id")
                )

                if movie_id in existing_ids:
                    continue

                final_movies.append(
                    movie
                )

                existing_ids.add(
                    movie_id
                )

                if len(final_movies) >= 30:
                    break

    # --------------------------------------------------------
    # FINAL SHUFFLE
    # --------------------------------------------------------

    random.shuffle(
        final_movies
    )

    # --------------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------------

    hindi_count = sum(
        1
        for movie in final_movies
        if movie.get(
            "recommendation_language"
        ) == "hi"
    )

    english_count = sum(
        1
        for movie in final_movies
        if movie.get(
            "recommendation_language"
        ) == "en"
    )

    print("=" * 60)

    print(
        "FINAL RECOMMENDATION BALANCE"
    )

    print(
        "Total:",
        len(final_movies)
    )

    print(
        "Hindi:",
        hindi_count
    )

    print(
        "English:",
        english_count
    )

    print("=" * 60)

    return final_movies[:30]


# ============================================================
# GET LANGUAGES + GENRES FROM USER ENGAGEMENT
# ============================================================

def get_user_preferences(user_id):

    activity = get_user_activity(
        user_id
    )

    interacted_ids = set(
        activity["watchlist"]
        +
        activity["history"]
        +
        [
            item["movie_id"]
            for item in activity["trailer_activity"]
        ]
    )

    languages = set()

    genre_ids = set()

    # --------------------------------------------------------
    # MOOD / LANGUAGE PREFERENCE ANALYSIS
    # --------------------------------------------------------

    for movie_id in interacted_ids:

        try:

            movie = get_movie_details(
                movie_id
            )

            if not movie:
                continue

            # ------------------------------------------------
            # ORIGINAL LANGUAGE
            # ------------------------------------------------

            language = movie.get(
                "original_language"
            )

            if language:

                languages.add(
                    language
                )

            # ------------------------------------------------
            # GENRES
            # ------------------------------------------------

            movie_genres = movie.get(
                "genres",
                []
            )

            if isinstance(
                movie_genres,
                list
            ):

                for genre in movie_genres:

                    genre_id = genre.get(
                        "id"
                    )

                    if genre_id:

                        genre_ids.add(
                            genre_id
                        )

        except Exception as e:

            print(
                "Preference analysis error:",
                movie_id,
                e
            )

    print("=" * 60)

    print(
        "USER PREFERENCES"
    )

    print(
        "User:",
        user_id
    )

    print(
        "Languages:",
        languages
    )

    print(
        "Genres:",
        genre_ids
    )

    print("=" * 60)

    return {

        "languages":
            languages,

        "genre_ids":
            genre_ids,

        "interacted_ids":
            interacted_ids

    }


# ============================================================
# AI MOVIE RECOMMENDATION SCORING
# ============================================================

def calculate_ai_scores(user_id):

    activity = get_user_activity(
        user_id
    )

    watchlist_ids = set(
        activity["watchlist"]
    )

    history_ids = set(
        activity["history"]
    )

    trailer_activity = (
        activity["trailer_activity"]
    )

    scores = {}

    # --------------------------------------------------------
    # TRAILER INTEREST
    # --------------------------------------------------------

    for item in trailer_activity:

        movie_id = item["movie_id"]

        watch_percentage = float(
            item.get(
                "watch_percentage",
                0
            ) or 0
        )

        if movie_id not in scores:

            scores[movie_id] = 0

        if watch_percentage >= 100:

            scores[movie_id] += 50

        elif watch_percentage >= 85:

            scores[movie_id] += 30

    # --------------------------------------------------------
    # WATCH HISTORY
    # --------------------------------------------------------

    for movie_id in history_ids:

        if movie_id not in scores:

            scores[movie_id] = 0

        scores[movie_id] += 25

    # --------------------------------------------------------
    # WATCHLIST
    # --------------------------------------------------------

    for movie_id in watchlist_ids:

        if movie_id not in scores:

            scores[movie_id] = 0

        scores[movie_id] += 20

    # --------------------------------------------------------
    # SORT BY SCORE
    # --------------------------------------------------------

    ranked_movies = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    print("=" * 60)

    print(
        "AI MOVIE SCORES"
    )

    print(
        "User ID:",
        user_id
    )

    for movie_id, score in ranked_movies:

        print(
            "Movie ID:",
            movie_id,
            "| Score:",
            score
        )

    print("=" * 60)

    return ranked_movies


# ============================================================
# SMART MOOD RECOMMENDATIONS
# ============================================================

def get_smart_mood_recommendations(
    user_id,
    mood,
    excluded_ids=None
):

    if excluded_ids is None:

        excluded_ids = set()

    else:

        excluded_ids = set(
            excluded_ids
        )

    # --------------------------------------------------------
    # MOOD → GENRES
    # --------------------------------------------------------

    mood_genres = {

        "cozy": [
            "Comedy",
            "Romance",
            "Family"
        ],

        "emotional": [
            "Drama",
            "Romance"
        ],

        "adrenaline": [
            "Action",
            "Thriller"
        ],

        "mystery": [
            "Mystery",
            "Thriller",
            "Crime"
        ],

        "horror": [
            "Horror",
            "Mystery",
            "Thriller"
        ],

        "fantasy": [
            "Fantasy",
            "Adventure"
        ],

        "romance": [
            "Romance",
            "Drama",
            "Comedy"
        ],

        "mind": [
            "Mystery",
            "Science Fiction",
            "Thriller"
        ],

        "funny": [
            "Comedy"
        ],

        "explore": [
            "Adventure",
            "Fantasy",
            "Science Fiction"
        ]
    }

    selected_genres = mood_genres.get(
        mood,
        []
    )

    # --------------------------------------------------------
    # CONVERT MOOD GENRES → IDS
    # --------------------------------------------------------

    mood_genre_ids = []

    for genre_id, genre_name in GENRES.items():

        if genre_name in selected_genres:

            mood_genre_ids.append(
                genre_id
            )

    # --------------------------------------------------------
    # GET USER PREFERENCES
    # --------------------------------------------------------

    preferences = get_user_preferences(
        user_id
    )

    user_languages = preferences[
        "languages"
    ]

    user_genres = preferences[
        "genre_ids"
    ]

    interacted_ids = preferences[
        "interacted_ids"
    ]

    # --------------------------------------------------------
    # EXCLUDED MOVIES
    # --------------------------------------------------------

    excluded_ids = (
        excluded_ids
        |
        interacted_ids
    )

    print("=" * 60)

    print(
        "SMART MOOD RECOMMENDATIONS"
    )

    print(
        "Mood:",
        mood
    )

    print(
        "Mood genres:",
        selected_genres
    )

    print(
        "User languages:",
        user_languages
    )

    print(
        "User genres:",
        user_genres
    )

    print(
        "Excluded:",
        len(excluded_ids)
    )

    print("=" * 60)

    # --------------------------------------------------------
    # CANDIDATE MOVIES
    # --------------------------------------------------------

    candidates = {}

    # ========================================================
    # SOURCE 1
    # MOOD + EACH USER LANGUAGE
    # ========================================================

    if user_languages:

        for language in user_languages:

            movies = discover_random_movies(
                genres=mood_genre_ids,
                language=language,
                pages=4
            )

            for movie in movies:

                movie_id = movie.get(
                    "id"
                )

                if not movie_id:
                    continue

                if movie_id in excluded_ids:
                    continue

                score = 100

                score += 40

                score += 50

                score += (
                    float(
                        movie.get(
                            "vote_average",
                            0
                        )
                    )
                    * 2
                )

                candidates[
                    movie_id
                ] = {

                    "movie":
                        movie,

                    "score":
                        score

                }

    # ========================================================
    # SOURCE 2
    # USER GENRES + EACH LANGUAGE
    # ========================================================

    combined_genres = list(
        set(
            mood_genre_ids
            +
            list(user_genres)
        )
    )

    if user_languages:

        for language in user_languages:

            movies = discover_random_movies(
                genres=combined_genres,
                language=language,
                pages=3
            )

            for movie in movies:

                movie_id = movie.get(
                    "id"
                )

                if not movie_id:
                    continue

                if movie_id in excluded_ids:
                    continue

                score = 80

                score += 45

                score += (
                    float(
                        movie.get(
                            "vote_average",
                            0
                        )
                    )
                    * 2
                )

                if movie_id in candidates:

                    candidates[
                        movie_id
                    ][
                        "score"
                    ] += score

                else:

                    candidates[
                        movie_id
                    ] = {

                        "movie":
                            movie,

                        "score":
                            score

                    }

    # ========================================================
    # SOURCE 3
    # MOOD MOVIES WITHOUT LANGUAGE RESTRICTION
    # ========================================================

    mood_movies = discover_random_movies(
        genres=mood_genre_ids,
        language=None,
        pages=6
    )

    for movie in mood_movies:

        movie_id = movie.get(
            "id"
        )

        if not movie_id:
            continue

        if movie_id in excluded_ids:
            continue

        score = 50

        score += (
            float(
                movie.get(
                    "vote_average",
                    0
                )
            )
            * 2
        )

        if movie_id in candidates:

            candidates[
                movie_id
            ][
                "score"
            ] += score

        else:

            candidates[
                movie_id
            ] = {

                "movie":
                    movie,

                "score":
                    score

            }

    # ========================================================
    # SOURCE 4
    # PURE LANGUAGE RECOMMENDATIONS
    # ========================================================

    if user_languages:

        for language in user_languages:

            language_movies = discover_random_movies(
                genres=None,
                language=language,
                pages=3
            )

            for movie in language_movies:

                movie_id = movie.get(
                    "id"
                )

                if not movie_id:
                    continue

                if movie_id in excluded_ids:
                    continue

                score = 35

                score += (
                    float(
                        movie.get(
                            "vote_average",
                            0
                        )
                    )
                    * 1.5
                )

                if movie_id in candidates:

                    candidates[
                        movie_id
                    ][
                        "score"
                    ] += score

                else:

                    candidates[
                        movie_id
                    ] = {

                        "movie":
                            movie,

                        "score":
                            score

                    }

    # ========================================================
    # SORT
    # ========================================================

    ranked = sorted(

        candidates.values(),

        key=lambda item:
            item["score"],

        reverse=True
    )

    # ========================================================
    # ADD RANDOMNESS
    # ========================================================

    top_pool = ranked[:80]

    random.shuffle(
        top_pool
    )

    for item in top_pool:

        item[
            "random_score"
        ] = (

            item["score"]

            +

            random.uniform(
                0,
                45
            )
        )

    top_pool.sort(

        key=lambda item:
            item["random_score"],

        reverse=True
    )

    # ========================================================
    # FINAL 30 MOVIES
    # ========================================================

    final_movies = []

    used_ids = set()

    for item in top_pool:

        movie = item[
            "movie"
        ]

        movie_id = movie.get(
            "id"
        )

        if not movie_id:
            continue

        if movie_id in used_ids:
            continue

        if movie_id in excluded_ids:
            continue

        movie[
            "ai_score"
        ] = item[
            "score"
        ]

        final_movies.append(
            movie
        )

        used_ids.add(
            movie_id
        )

        if len(
            final_movies
        ) >= 30:

            break

    # ========================================================
    # FINAL SHUFFLE
    # ========================================================

    random.shuffle(
        final_movies
    )

    print(
        "FINAL SMART RECOMMENDATIONS:",
        len(final_movies)
    )

    print(
        "Languages represented:"
    )

    language_counter = {}

    for movie in final_movies:

        lang = movie.get(
            "original_language",
            "unknown"
        )

        language_counter[
            lang
        ] = (
            language_counter.get(
                lang,
                0
            )
            + 1
        )

    print(
        language_counter
    )

    print("=" * 60)

    return final_movies


# ============================================================
# GET NEW AI RECOMMENDATIONS
# ============================================================

def get_ai_recommendations(user_id):

    print("=" * 60)

    print(
        "GENERATING NEW AI RECOMMENDATIONS"
    )

    print(
        "User ID:",
        user_id
    )

    # --------------------------------------------------------
    # GET USER ACTIVITY
    # --------------------------------------------------------

    activity = get_user_activity(
        user_id
    )

    watchlist_ids = set(
        activity["watchlist"]
    )

    history_ids = set(
        activity["history"]
    )

    trailer_activity = (
        activity["trailer_activity"]
    )

    # --------------------------------------------------------
    # ALL MOVIES USER ALREADY INTERACTED WITH
    # --------------------------------------------------------

    interacted_ids = (

        watchlist_ids

        |

        history_ids

        |

        {
            item["movie_id"]
            for item in trailer_activity
        }

    )

    print(
        "Already interacted movies:",
        len(interacted_ids)
    )

    # --------------------------------------------------------
    # GET AI SCORES
    # --------------------------------------------------------

    ranked_movies = calculate_ai_scores(
        user_id
    )

    # --------------------------------------------------------
    # TOP 5 SEED MOVIES
    # --------------------------------------------------------

    seed_movies = ranked_movies[:5]

    print(
        "Seed movies:"
    )

    for movie_id, score in seed_movies:

        print(
            "Movie ID:",
            movie_id,
            "| Score:",
            score
        )

    # --------------------------------------------------------
    # FIND SIMILAR MOVIES
    # --------------------------------------------------------

    candidates = {}

    for movie_id, score in seed_movies:

        try:

            similar_movies = get_similar_movies(
                movie_id
            )

            for movie in similar_movies:

                recommended_id = movie.get(
                    "tmdb_id",
                    movie.get("id")
                )

                if not recommended_id:
                    continue

                if recommended_id in interacted_ids:
                    continue

                if recommended_id not in candidates:

                    candidates[
                        recommended_id
                    ] = {

                        "movie":
                            movie,

                        "recommendation_score":
                            score

                    }

                else:

                    candidates[
                        recommended_id
                    ][
                        "recommendation_score"
                    ] += score

        except Exception as e:

            print(
                "Recommendation Error:",
                movie_id,
                e
            )

    # --------------------------------------------------------
    # SORT CANDIDATES
    # --------------------------------------------------------

    ranked_candidates = sorted(

        candidates.values(),

        key=lambda item:
            item[
                "recommendation_score"
            ],

        reverse=True
    )

    # --------------------------------------------------------
    # PREPARE FINAL MOVIES
    # --------------------------------------------------------

    ai_movies = []

    for item in ranked_candidates[:10]:

        movie = item["movie"]

        movie["ai_score"] = item[
            "recommendation_score"
        ]

        genre_text = movie.get(
            "genres",
            ""
        )

        if isinstance(
            genre_text,
            str
        ):

            movie["genres"] = [

                {
                    "name":
                        genre.strip()
                }

                for genre in
                genre_text.split(",")

                if genre.strip()

            ]

        ai_movies.append(
            movie
        )

    print(
        "New recommendations:",
        len(ai_movies)
    )

    print("=" * 60)

    return ai_movies


# ============================================================
# FETCH TMDB
# ============================================================

def fetch_tmdb(
    url,
    params
):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(3):

        try:

            response = tmdb_session.get(
                url,
                params=params,
                headers=headers,
                timeout=20
            )

            response.raise_for_status()

            return response.json().get(
                "results",
                []
            )

        except requests.exceptions.RequestException as e:

            print(
                f"Attempt {attempt + 1} failed:",
                e
            )

            if attempt < 2:

                time.sleep(2)

            else:

                raise


# ============================================================
# RESOLVE MOVIE ID
# ============================================================

def resolve_tmdb_movie_id(movie_id):

    try:

        movie_id = int(
            movie_id
        )

    except (
        TypeError,
        ValueError
    ):

        return movie_id

    try:

        movies = get_all_movies()

        for movie in movies:

            try:
                local_id = movie["id"]
            except (
                KeyError,
                TypeError
            ):
                local_id = None

            try:
                tmdb_id = movie["tmdb_id"]
            except (
                KeyError,
                TypeError
            ):
                tmdb_id = None

            if local_id is not None:

                try:

                    if int(local_id) == movie_id:

                        if tmdb_id:

                            print("=" * 60)

                            print(
                                "MOVIE ID RESOLUTION"
                            )

                            print(
                                "Local ID:",
                                movie_id
                            )

                            print(
                                "TMDB ID:",
                                tmdb_id
                            )

                            print("=" * 60)

                            return int(
                                tmdb_id
                            )

                except (
                    TypeError,
                    ValueError
                ):

                    pass

    except Exception as e:

        print(
            "Movie ID resolution error:",
            e
        )

    return movie_id


# ============================================================
# GET MOVIE DETAILS
# ============================================================

def get_movie_details(movie_id):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}"
    )

    params = {

        "api_key":
            TMDB_API_KEY,

        "language":
            "en-US"

    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(3):

        try:

            response = tmdb_session.get(
                url,
                params=params,
                headers=headers,
                timeout=20
            )

            response.raise_for_status()

            movie = response.json()

            # =================================================
            # LANGUAGE
            # =================================================

            try:

                code = movie.get(
                    "original_language",
                    "en"
                )

                movie[
                    "language_name"
                ] = Locale("en").languages.get(
                    code,
                    code.upper()
                )

            except Exception:

                movie[
                    "language_name"
                ] = movie.get(
                    "original_language",
                    "Unknown"
                ).upper()

            # =================================================
            # IMAGE URLS
            # =================================================

            movie["backdrop_url"] = (

                f"https://image.tmdb.org/t/p/original"
                f"{movie['backdrop_path']}"

                if movie.get(
                    "backdrop_path"
                )

                else ""

            )

            movie["poster_url"] = (

                f"https://image.tmdb.org/t/p/w500"
                f"{movie['poster_path']}"

                if movie.get(
                    "poster_path"
                )

                else ""

            )

            # =================================================
            # RELEASE TYPE
            # =================================================

            movie[
                "release_type"
            ] = "Unknown"

            try:

                release_url = (

                    f"https://api.themoviedb.org/3/movie/"
                    f"{movie_id}/release_dates"

                )

                release_response = tmdb_session.get(
                    release_url,
                    params={
                        "api_key":
                            TMDB_API_KEY
                    },
                    headers=headers,
                    timeout=20
                )

                release_response.raise_for_status()

                release_data = (
                    release_response.json()
                )

                preferred = [
                    "IN",
                    "US"
                ]

                country_data = None

                for country in preferred:

                    country_data = next(

                        (
                            item

                            for item in
                            release_data.get(
                                "results",
                                []
                            )

                            if item.get(
                                "iso_3166_1"
                            ) == country
                        ),

                        None
                    )

                    if country_data:
                        break

                if (
                    not country_data
                    and
                    release_data.get(
                        "results"
                    )
                ):

                    country_data = (
                        release_data[
                            "results"
                        ][0]
                    )

                if country_data:

                    for release in country_data.get(
                        "release_dates",
                        []
                    ):

                        release_type = (
                            release.get(
                                "type"
                            )
                        )

                        if release_type == 3:

                            movie[
                                "release_type"
                            ] = "Theatrical 🎬"

                            break

                        elif release_type == 4:

                            movie[
                                "release_type"
                            ] = "OTT Release 📺"

                        elif release_type == 5:

                            movie[
                                "release_type"
                            ] = "Physical 💿"

            except requests.exceptions.RequestException:

                pass

            # =================================================
            # OTT PROVIDERS
            # =================================================

            movie[
                "ott_platforms"
            ] = []

            providers = {}

            try:

                provider_url = (

                    f"https://api.themoviedb.org/3/movie/"
                    f"{movie_id}/watch/providers"

                )

                provider_response = tmdb_session.get(
                    provider_url,
                    params={
                        "api_key":
                            TMDB_API_KEY
                    },
                    headers=headers,
                    timeout=20
                )

                provider_response.raise_for_status()

                provider_data = (
                    provider_response.json()
                )

                country = (
                    provider_data.get(
                        "results",
                        {}
                    ).get("IN")
                )

                if not country:

                    country = (
                        provider_data.get(
                            "results",
                            {}
                        ).get("US")
                    )

                if country:

                    # ----------------------------------------
                    # STREAMING
                    # ----------------------------------------

                    for provider in country.get(
                        "flatrate",
                        []
                    ):

                        name = provider.get(
                            "provider_name"
                        )

                        if name not in providers:

                            providers[name] = {

                                "name":
                                    name,

                                "logo": (
                                    f"https://image.tmdb.org/t/p/w200"
                                    f"{provider.get('logo_path', '')}"
                                ),

                                "types": []

                            }

                        if (
                            "Streaming"
                            not in
                            providers[name]["types"]
                        ):

                            providers[
                                name
                            ][
                                "types"
                            ].append(
                                "Streaming"
                            )

                    # ----------------------------------------
                    # RENT
                    # ----------------------------------------

                    for provider in country.get(
                        "rent",
                        []
                    ):

                        name = provider.get(
                            "provider_name"
                        )

                        if name not in providers:

                            providers[name] = {

                                "name":
                                    name,

                                "logo": (
                                    f"https://image.tmdb.org/t/p/w200"
                                    f"{provider.get('logo_path', '')}"
                                ),

                                "types": []

                            }

                        if (
                            "Rent"
                            not in
                            providers[name]["types"]
                        ):

                            providers[
                                name
                            ][
                                "types"
                            ].append(
                                "Rent"
                            )

                    # ----------------------------------------
                    # BUY
                    # ----------------------------------------

                    for provider in country.get(
                        "buy",
                        []
                    ):

                        name = provider.get(
                            "provider_name"
                        )

                        if name not in providers:

                            providers[name] = {

                                "name":
                                    name,

                                "logo": (
                                    f"https://image.tmdb.org/t/p/w200"
                                    f"{provider.get('logo_path', '')}"
                                ),

                                "types": []

                            }

                        if (
                            "Buy"
                            not in
                            providers[name]["types"]
                        ):

                            providers[
                                name
                            ][
                                "types"
                            ].append(
                                "Buy"
                            )

                    movie[
                        "ott_platforms"
                    ] = list(
                        providers.values()
                    )

                    movie[
                        "watch_link"
                    ] = country.get(
                        "link",
                        ""
                    )

                else:

                    movie[
                        "watch_link"
                    ] = ""

            except requests.exceptions.RequestException:

                movie[
                    "watch_link"
                ] = ""

            # =================================================
            # TOP CAST
            # =================================================

            movie["cast"] = []

            try:

                credits_url = (

                    f"https://api.themoviedb.org/3/movie/"
                    f"{movie_id}/credits"

                )

                print(
                    "Fetching Credits..."
                )

                credits_response = tmdb_session.get(
                    credits_url,
                    params={
                        "api_key":
                            TMDB_API_KEY
                    },
                    headers=headers,
                    timeout=20
                )

                credits_response.raise_for_status()

                credits_data = (
                    credits_response.json()
                )

                print(
                    "Movie ID:",
                    movie_id
                )

                print(
                    "Cast returned:",
                    len(
                        credits_data.get(
                            "cast",
                            []
                        )
                    )
                )

                for actor in credits_data.get(
                    "cast",
                    []
                )[:10]:

                    if not actor.get(
                        "profile_path"
                    ):

                        continue

                    movie[
                        "cast"
                    ].append({

                        "name":
                            actor.get(
                                "name",
                                "Unknown"
                            ),

                        "character":
                            actor.get(
                                "character",
                                "Unknown"
                            ),

                        "profile": (
                            f"https://image.tmdb.org/t/p/w300"
                            f"{actor['profile_path']}"
                        )

                    })

            except Exception:

                import traceback

                print("=" * 60)

                print(
                    "CAST REQUEST FAILED"
                )

                traceback.print_exc()

                print("=" * 60)

            print(
                "Cast after filtering:",
                len(
                    movie["cast"]
                )
            )

            # =================================================
            # TRAILER
            # =================================================

            movie[
                "trailer_key"
            ] = None

            try:

                video_url = (

                    f"https://api.themoviedb.org/3/movie/"
                    f"{movie_id}/videos"

                )

                video_response = tmdb_session.get(
                    video_url,
                    params={
                        "api_key":
                            TMDB_API_KEY,

                        "language":
                            "en-US"
                    },
                    headers=headers,
                    timeout=20
                )

                video_response.raise_for_status()

                videos = (
                    video_response.json().get(
                        "results",
                        []
                    )
                )

                # --------------------------------------------
                # OFFICIAL TRAILER
                # --------------------------------------------

                for video in videos:

                    if (

                        video.get(
                            "site"
                        ) == "YouTube"

                        and

                        video.get(
                            "type"
                        ) == "Trailer"

                        and

                        video.get(
                            "key"
                        )

                    ):

                        movie[
                            "trailer_key"
                        ] = video[
                            "key"
                        ]

                        break

                # --------------------------------------------
                # TEASER
                # --------------------------------------------

                if not movie[
                    "trailer_key"
                ]:

                    for video in videos:

                        if (

                            video.get(
                                "site"
                            ) == "YouTube"

                            and

                            video.get(
                                "type"
                            ) == "Teaser"

                            and

                            video.get(
                                "key"
                            )

                        ):

                            movie[
                                "trailer_key"
                            ] = video[
                                "key"
                            ]

                            break

                # --------------------------------------------
                # ANY YOUTUBE VIDEO
                # --------------------------------------------

                if not movie[
                    "trailer_key"
                ]:

                    for video in videos:

                        if (

                            video.get(
                                "site"
                            ) == "YouTube"

                            and

                            video.get(
                                "key"
                            )

                        ):

                            movie[
                                "trailer_key"
                            ] = video[
                                "key"
                            ]

                            break

            except Exception as e:

                print(
                    "Trailer Error:",
                    e
                )

            # =================================================
            # RETURN MOVIE
            # =================================================

            return movie

        except requests.exceptions.RequestException as e:

            print(
                f"TMDB Request Error "
                f"(attempt {attempt + 1}/3):",
                e
            )

            if attempt < 2:

                time.sleep(2)

            else:

                return {}


# ============================================================
# SIMILAR MOVIES
# ============================================================

def get_similar_movies(movie_id):

    print("=" * 60)

    print(
        "get_similar_movies() called"
    )

    print(
        "Movie ID:",
        movie_id
    )

    similar_movies = []

    try:

        # =====================================================
        # FIRST TRY — SIMILAR MOVIES
        # =====================================================

        url = (
            f"{TMDB_BASE_URL}/movie/"
            f"{movie_id}/similar"
        )

        params = {

            "api_key":
                TMDB_API_KEY,

            "language":
                "en-US",

            "page":
                1

        }

        similar_movies = fetch_tmdb(
            url,
            params
        )

        print(
            "Similar movies returned:",
            len(similar_movies)
        )

        # =====================================================
        # SECOND TRY — RECOMMENDATIONS
        # =====================================================

        if not similar_movies:

            print(
                "No similar movies found."
            )

            print(
                "Trying recommendations..."
            )

            url = (
                f"{TMDB_BASE_URL}/movie/"
                f"{movie_id}/recommendations"
            )

            similar_movies = fetch_tmdb(
                url,
                params
            )

            print(
                "Recommendations returned:",
                len(similar_movies)
            )

        # =====================================================
        # FORMAT MOVIES
        # =====================================================

        formatted_movies = []

        for movie in similar_movies:

            tmdb_id = movie.get(
                "id"
            )

            if not tmdb_id:
                continue

            if tmdb_id == movie_id:
                continue

            poster_path = movie.get(
                "poster_path"
            )

            if poster_path:

                poster_url = (
                    "https://image.tmdb.org/t/p/w500"
                    +
                    poster_path
                )

            else:

                poster_url = ""

            backdrop_path = movie.get(
                "backdrop_path"
            )

            if backdrop_path:

                backdrop_url = (
                    "https://image.tmdb.org/t/p/original"
                    +
                    backdrop_path
                )

            else:

                backdrop_url = ""

            rating = movie.get(
                "vote_average",
                0
            )

            genre_ids = movie.get(
                "genre_ids",
                []
            )

            genre_names = [

                GENRES[g]

                for g in genre_ids

                if g in GENRES

            ]

            genres = ", ".join(
                genre_names
            )

            formatted_movie = {

                "id":
                    tmdb_id,

                "tmdb_id":
                    tmdb_id,

                "title":
                    movie.get(
                        "title",
                        "Unknown Movie"
                    ),

                "poster_path":
                    poster_path,

                "poster_url":
                    poster_url,

                "backdrop_path":
                    backdrop_path,

                "backdrop_url":
                    backdrop_url,

                "release_date":
                    movie.get(
                        "release_date",
                        ""
                    ),

                "vote_average":
                    rating,

                "rating":
                    rating,

                "vote_rating":
                    rating,

                "genre_ids":
                    genre_ids,

                "genre_names":
                    genre_names,

                "genres":
                    genres

            }

            formatted_movies.append(
                formatted_movie
            )

        # =====================================================
        # FALLBACK — DISCOVER BY GENRE
        # =====================================================

        if not formatted_movies:

            print(
                "No similar/recommended movies."
            )

            print(
                "Trying genre-based fallback..."
            )

            original_movie = get_movie_details(
                movie_id
            )

            original_genres = (
                original_movie.get(
                    "genres",
                    []
                )
            )

            original_genre_ids = [

                genre.get("id")

                for genre in original_genres

                if genre.get("id")

            ]

            if original_genre_ids:

                discover_url = (
                    f"{TMDB_BASE_URL}/discover/movie"
                )

                discover_params = {

                    "api_key":
                        TMDB_API_KEY,

                    "language":
                        "en-US",

                    "sort_by":
                        "popularity.desc",

                    "include_adult":
                        False,

                    "with_genres":
                        ",".join(
                            str(g)
                            for g in original_genre_ids
                        ),

                    "page":
                        1

                }

                fallback_movies = fetch_tmdb(
                    discover_url,
                    discover_params
                )

                for movie in fallback_movies:

                    tmdb_id = movie.get(
                        "id"
                    )

                    if not tmdb_id:
                        continue

                    if tmdb_id == movie_id:
                        continue

                    poster_path = movie.get(
                        "poster_path"
                    )

                    if poster_path:

                        poster_url = (
                            "https://image.tmdb.org/t/p/w500"
                            +
                            poster_path
                        )

                    else:

                        poster_url = ""

                    rating = movie.get(
                        "vote_average",
                        0
                    )

                    genre_ids = movie.get(
                        "genre_ids",
                        []
                    )

                    genre_names = [

                        GENRES[g]

                        for g in genre_ids

                        if g in GENRES

                    ]

                    formatted_movies.append({

                        "id":
                            tmdb_id,

                        "tmdb_id":
                            tmdb_id,

                        "title":
                            movie.get(
                                "title",
                                "Unknown Movie"
                            ),

                        "poster_path":
                            poster_path,

                        "poster_url":
                            poster_url,

                        "backdrop_path":
                            movie.get(
                                "backdrop_path"
                            ),

                        "backdrop_url":
                            "",

                        "release_date":
                            movie.get(
                                "release_date",
                                ""
                            ),

                        "vote_average":
                            rating,

                        "rating":
                            rating,

                        "vote_rating":
                            rating,

                        "genre_ids":
                            genre_ids,

                        "genre_names":
                            genre_names,

                        "genres":
                            ", ".join(
                                genre_names
                            )

                    })

        # =====================================================
        # FIRST 10
        # =====================================================

        formatted_movies = (
            formatted_movies[:10]
        )

        print(
            "Returning",
            len(formatted_movies),
            "formatted movies"
        )

        print("=" * 60)

        return formatted_movies

    except Exception as e:

        import traceback

        print("=" * 60)

        print(
            "SIMILAR MOVIES ERROR"
        )

        traceback.print_exc()

        print("=" * 60)

        return []


# ============================================================
# TRENDING MOVIES
# ============================================================

def get_trending_movies():

    print(
        "Loading Trending..."
    )

    today = datetime.today().date()

    released = []

    try:

        url = (
            f"{TMDB_BASE_URL}/trending/movie/week"
        )

        movies = []

        for page in range(1, 26):

            params = {

                "api_key":
                    TMDB_API_KEY,

                "page":
                    page

            }

            print(
                f"Fetching Trending Page {page}..."
            )

            movies.extend(
                fetch_tmdb(
                    url,
                    params
                )
            )

        seen = set()

        for movie in movies:

            if movie["id"] in seen:
                continue

            seen.add(
                movie["id"]
            )

            if movie.get(
                "release_date"
            ):

                release = datetime.strptime(
                    movie[
                        "release_date"
                    ],
                    "%Y-%m-%d"
                ).date()

                if release <= today:

                    released.append(
                        movie
                    )

        for movie in released:

            movie["poster_url"] = (

                f"https://image.tmdb.org/t/p/w500"
                f"{movie['poster_path']}"

                if movie.get(
                    "poster_path"
                )

                else ""

            )

            movie[
                "genre_names"
            ] = [

                GENRES[genre_id]

                for genre_id
                in movie.get(
                    "genre_ids",
                    []
                )

                if genre_id in GENRES

            ]

        print(
            "Released Movies:",
            len(released)
        )

        return released

    except Exception as e:

        print(
            "Trending ERROR:",
            e
        )

        return []


# ============================================================
# UPCOMING / NEW RELEASES
# ============================================================

# ============================================================
# NEW RELEASES
# ============================================================

def get_upcoming_movies(limit=20):

    print("=" * 60)
    print("LOADING NEW RELEASES")
    print("=" * 60)

    url = f"{TMDB_BASE_URL}/discover/movie"

    from datetime import datetime, timedelta

    today = datetime.today().date()

# Look back 180 days for recently released movies
    past_date = today - timedelta(days=180)

    collected = []
    seen_ids = set()

    # --------------------------------------------------------
    # FETCH MULTIPLE PAGES
    # --------------------------------------------------------

    for page in range(1, 11):

        if len(collected) >= limit:
            break

        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "sort_by": "primary_release_date.asc",
            "include_adult": False,
            "include_video": False,
            "page": page,

            "primary_release_date.gte":
             past_date.strftime("%Y-%m-%d"),

            "primary_release_date.lte":
            today.strftime("%Y-%m-%d"),

            "vote_count.gte": 1
        }

        try:

            print(
                f"Fetching New Releases Page {page}..."
            )

            movies = fetch_tmdb(
                url,
                params
            )

            print(
                f"Page {page}: {len(movies)} results"
            )

            for movie in movies:

                movie_id = movie.get("id")

                if not movie_id:
                    continue

                if movie_id in seen_ids:
                    continue

                seen_ids.add(movie_id)

                release_date = movie.get(
                    "release_date",
                    ""
                )

                if not release_date:
                    continue


                # ------------------------------------------------
                # POSTER REQUIRED
                # ------------------------------------------------

                if not movie.get("poster_path"):
                    continue

                # ------------------------------------------------
                # FORMAT
                # ------------------------------------------------

                movie["tmdb_id"] = movie_id

                movie["poster_url"] = (
                    "https://image.tmdb.org/t/p/w500"
                    + movie["poster_path"]
                )

                movie["backdrop_url"] = (
                    "https://image.tmdb.org/t/p/original"
                    + movie["backdrop_path"]
                    if movie.get("backdrop_path")
                    else ""
                )

                movie["rating"] = movie.get(
                    "vote_average",
                    0
                )

                movie["language"] = movie.get(
                    "original_language",
                    ""
                )

                movie["genre_names"] = [
                    GENRES[g]
                    for g in movie.get(
                        "genre_ids",
                        []
                    )
                    if g in GENRES
                ]

                movie["genres"] = ", ".join(
                    movie["genre_names"]
                )

                collected.append(movie)

                if len(collected) >= limit:
                    break

        except Exception as e:

            print(
                f"New Releases Page {page} Error:",
                e
            )

            continue

    # --------------------------------------------------------
    # SORT BY RELEASE DATE
    # --------------------------------------------------------

    collected.sort(
        key=lambda movie:
            movie.get(
                "release_date",
                "9999-12-31"
            )
    )

    collected = collected[:limit]

    print("=" * 60)
    print(
        "FINAL NEW RELEASES:",
        len(collected)
    )

    for movie in collected:
        print(
            movie.get("title"),
            "|",
            movie.get("release_date")
        )

    print("=" * 60)

    return collected

def sync_movies_to_database(movies):

    for movie in movies:

        try:

            insert_movie(movie)

        except Exception as e:

            print(
                "Movie database sync error:",
                movie.get("title"),
                e
            )

# ============================================================
# TOP RATED MOVIES
# ============================================================

def get_top_rated_movies():

    print(
        "Loading Top Rated..."
    )

    url = (
        f"{TMDB_BASE_URL}/movie/top_rated"
    )

    params = {

        "api_key":
            TMDB_API_KEY

    }

    try:

        movies = fetch_tmdb(
            url,
            params
        )

        for movie in movies:

            print(
                movie["title"],
                movie.get(
                    "genre_ids"
                )
            )

            movie[
                "genre_names"
            ] = [

                GENRES[genre_id]

                for genre_id
                in movie.get(
                    "genre_ids",
                    []
                )

                if genre_id in GENRES

            ]

        return movies[:25]

    except Exception as e:

        print(
            "Top Rated ERROR:",
            e
        )

        return []


# ============================================================
# DISCOVER MOVIES
# ============================================================

def discover_movies(
    genres=None,
    language=None,
    page=1
):

    url = (
        f"{TMDB_BASE_URL}/discover/movie"
    )

    params = {

        "api_key":
            TMDB_API_KEY,

        "language":
            "en-US",

        "sort_by":
            "popularity.desc",

        "include_adult":
            False

    }

    # --------------------------------------------------------
    # GENRES
    # --------------------------------------------------------

    if genres:

        params["with_genres"] = "|".join(
            str(g)
            for g in genres
        )

    # --------------------------------------------------------
    # ORIGINAL LANGUAGE
    # --------------------------------------------------------

    if language:

        params[
            "with_original_language"
        ] = language

    try:

        all_movies = []

        start_page = page

        end_page = page + 4

        for current_page in range(
            start_page,
            end_page + 1
        ):

            params[
                "page"
            ] = current_page

            all_movies.extend(
                fetch_tmdb(
                    url,
                    params
                )
            )

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        unique_movies = []

        seen_ids = set()

        for movie in all_movies:

            if movie["id"] in seen_ids:
                continue

            seen_ids.add(
                movie["id"]
            )

            unique_movies.append(
                movie
            )

        movies = unique_movies

        # ----------------------------------------------------
        # FORMAT MOVIES
        # ----------------------------------------------------

        for movie in movies:

            movie[
                "tmdb_id"
            ] = movie["id"]

            movie[
                "poster_url"
            ] = (

                f"https://image.tmdb.org/t/p/w500"
                f"{movie['poster_path']}"

                if movie.get(
                    "poster_path"
                )

                else ""

            )

            movie[
                "backdrop_url"
            ] = (

                f"https://image.tmdb.org/t/p/original"
                f"{movie['backdrop_path']}"

                if movie.get(
                    "backdrop_path"
                )

                else ""

            )

            movie[
                "rating"
            ] = movie.get(
                "vote_average",
                0
            )

            movie[
                "genres"
            ] = ", ".join(

                GENRES[g]

                for g
                in movie.get(
                    "genre_ids",
                    []
                )

                if g in GENRES

            )

        return movies

    except Exception as e:

        print(
            "Discover Error:",
            e
        )

        return []


# ============================================================
# RANDOM DISCOVER MOVIES
# ============================================================

def discover_random_movies(
    genres=None,
    language=None,
    pages=5
):

    url = (
        f"{TMDB_BASE_URL}/discover/movie"
    )

    all_movies = []

    # --------------------------------------------------------
    # RANDOM PAGES
    # --------------------------------------------------------

    random_pages = random.sample(
        range(1, 30),
        min(pages, 29)
    )

    for page in random_pages:

        params = {

            "api_key":
                TMDB_API_KEY,

            "language":
                "en-US",

            "sort_by":
                random.choice([
                    "popularity.desc",
                    "vote_average.desc",
                    "primary_release_date.desc"
                ]),

            "include_adult":
                False,

            "page":
                page,

            "vote_count.gte":
                20

        }

        # ----------------------------------------------------
        # GENRE FILTER
        # ----------------------------------------------------

        if genres:

            params["with_genres"] = "|".join(
                str(g)
                for g in genres
            )

        # ----------------------------------------------------
        # LANGUAGE FILTER
        # ----------------------------------------------------

        if language:

            params[
                "with_original_language"
            ] = language

        try:

            movies = fetch_tmdb(
                url,
                params
            )

            all_movies.extend(
                movies
            )

        except Exception as e:

            print(
                "Random discover error:",
                e
            )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_movies = []

    seen_ids = set()

    for movie in all_movies:

        movie_id = movie.get(
            "id"
        )

        if not movie_id:
            continue

        if movie_id in seen_ids:
            continue

        seen_ids.add(
            movie_id
        )

        # ----------------------------------------------------
        # REQUIRE POSTER
        # ----------------------------------------------------

        if not movie.get(
            "poster_path"
        ):

            continue

        movie[
            "tmdb_id"
        ] = movie_id

        movie[
            "poster_url"
        ] = (

            "https://image.tmdb.org/t/p/w500"
            +
            movie["poster_path"]

        )

        movie[
            "backdrop_url"
        ] = (

            "https://image.tmdb.org/t/p/original"
            +
            movie["backdrop_path"]

            if movie.get(
                "backdrop_path"
            )

            else ""

        )

        movie[
            "rating"
        ] = movie.get(
            "vote_average",
            0
        )

        movie[
            "genre_names"
        ] = [

            GENRES[g]

            for g in movie.get(
                "genre_ids",
                []
            )

            if g in GENRES

        ]

        movie[
            "genres"
        ] = ", ".join(
            movie["genre_names"]
        )

        movie[
            "original_language"
        ] = movie.get(
            "original_language",
            ""
        )

        unique_movies.append(
            movie
        )

    # --------------------------------------------------------
    # SHUFFLE
    # --------------------------------------------------------

    random.shuffle(
        unique_movies
    )

    return unique_movies


# ============================================================
# SEARCH TMDB MOVIES
# ============================================================

def search_tmdb_movies(
    query,
    page=1
):

    url = (
        f"{TMDB_BASE_URL}/search/movie"
    )

    params = {

        "api_key":
            TMDB_API_KEY,

        "language":
            "en-US",

        "query":
            query,

        "page":
            page,

        "include_adult":
            False

    }

    try:

        movies = fetch_tmdb(
            url,
            params
        )

        # ----------------------------------------------------
        # REMOVE INVALID / UNRELEASED MOVIES
        # ----------------------------------------------------

        movies = [

            movie

            for movie in movies

            if movie.get(
                "release_date"
            )

            and

            movie.get(
                "vote_count",
                0
            ) > 0

        ]

        for movie in movies:

            # ------------------------------------------------
            # SKIP MOVIES WITHOUT POSTER
            # ------------------------------------------------

            if not movie.get(
                "poster_path"
            ):

                continue

            movie[
                "poster_url"
            ] = (

                f"https://image.tmdb.org/t/p/w500"
                f"{movie['poster_path']}"

            )

            movie[
                "backdrop_url"
            ] = (

                f"https://image.tmdb.org/t/p/original"
                f"{movie['backdrop_path']}"

                if movie.get(
                    "backdrop_path"
                )

                else ""

            )

            movie[
                "rating"
            ] = movie.get(
                "vote_average",
                0
            )

            movie[
                "tmdb_id"
            ] = movie["id"]

            movie[
                "genres"
            ] = ", ".join(

                GENRES[g]

                for g in movie.get(
                    "genre_ids",
                    []
                )

                if g in GENRES

            )

        return movies

    except Exception as e:

        print(
            "Search Error:",
            e
        )

        return []


# ============================================================
# HOME
# ============================================================

# ============================================================
# HOME
# ============================================================

# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    # ========================================================
    # TRENDING
    # ========================================================

    movies = get_trending_movies_db(
        limit=20
    )


    # ========================================================
    # NEW RELEASES
    # ========================================================

    upcoming_movies = get_upcoming_movies(
        limit=20
    )


    # ========================================================
    # TOP RATED
    # ========================================================

    top_rated_movies = get_top_rated_movies_db(
        limit=20
    )


    # ========================================================
    # ACTION
    # ========================================================

    action_movies = get_movies_by_genre_limit(
        "Action",
        limit=20
    )


    # ========================================================
    # COMEDY
    # ========================================================

    comedy_movies = get_movies_by_genre_limit(
        "Comedy",
        limit=20
    )


    # ========================================================
    # ROMANCE
    # ========================================================

    romance_movies = get_movies_by_genre_limit(
        "Romance",
        limit=20
    )


    # ========================================================
    # THRILLER
    # ========================================================

    thriller_movies = get_movies_by_genre_limit(
        "Thriller",
        limit=20
    )


    # ========================================================
    # HERO POSTER CLOUD
    # ========================================================

    hero_sources = (
        movies
        + upcoming_movies
        + top_rated_movies
        + action_movies
        + comedy_movies
        + romance_movies
        + thriller_movies
    )


    hero_movies = []

    hero_seen_ids = set()


    for movie in hero_sources:

        movie_id = movie.get(
            "tmdb_id",
            movie.get("id")
        )

        if not movie_id:
            continue


        if movie_id in hero_seen_ids:
            continue


        poster = (
            movie.get("poster_url")
            or movie.get("poster_path")
        )


        if not poster:
            continue


        hero_seen_ids.add(movie_id)

        hero_movies.append(movie)


        if len(hero_movies) >= 30:
            break


    # ========================================================
    # DEBUG
    # ========================================================

    print("=" * 60)

    print("HOME PAGE")

    print(
        "Trending:",
        len(movies)
    )

    print(
        "New Releases:",
        len(upcoming_movies)
    )

    print(
        "Top Rated:",
        len(top_rated_movies)
    )

    print(
        "Action:",
        len(action_movies)
    )

    print(
        "Comedy:",
        len(comedy_movies)
    )

    print(
        "Romance:",
        len(romance_movies)
    )

    print(
        "Thriller:",
        len(thriller_movies)
    )

    print(
        "Hero Poster Cloud:",
        len(hero_movies)
    )

    print("=" * 60)


    # ========================================================
    # RENDER HOME PAGE
    # ========================================================

    return render_template(

        "home.html",

        hero_movies=hero_movies,

        movies=movies,

        upcoming_movies=upcoming_movies,

        top_rated_movies=top_rated_movies,

        action_movies=action_movies,

        comedy_movies=comedy_movies,

        romance_movies=romance_movies,

        thriller_movies=thriller_movies,

        genres=GENRES

    )
# ============================================================
# WATCHLIST
# ============================================================

@app.route("/watchlist")
def watchlist():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT movie_id
        FROM watchlist
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    watchlist_movies = []

    for row in rows:

        movie_id = row[
            "movie_id"
        ]

        try:

            movie = get_movie_details(
                movie_id
            )

            if movie:

                watchlist_movies.append(
                    movie
                )

        except Exception as e:

            print(
                "Watchlist movie error:",
                e
            )

    return render_template(

        "watchlist.html",

        watchlist_movies=
            watchlist_movies,

        active_page=
            "watchlist"

    )


# ============================================================
# MOVIES
# ============================================================

@app.route("/movies")
def movies():

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_genres = (
        request.args.getlist(
            "genres"
        )
    )

    selected_languages = (
        request.args.getlist(
            "languages"
        )
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        movies = search_tmdb_movies(
            search
        )

    # --------------------------------------------------------
    # GENRE / LANGUAGE
    # --------------------------------------------------------

    else:

        genre_ids = []

        for genre_name in selected_genres:

            for genre_id, name in GENRES.items():

                if name == genre_name:

                    genre_ids.append(
                        genre_id
                    )

                    break

        language_map = {

            "bollywood": "hi",

            "korean": "ko",

            "anime": "ja",

            "hollywood": "en",

            "chinese": "zh",

            "spanish": "es",

            "french": "fr",

            "thai": "th"

        }

        language_code = None

        if selected_languages:

            language_code = (
                language_map.get(
                    selected_languages[0]
                )
            )

        movies = discover_movies(

            genres=
                genre_ids
                if genre_ids
                else None,

            language=
                language_code

        )

    return render_template(

        "movies.html",

        movies=movies,

        genres=GENRES,

        active_page="movies",

        search=search,

        selected_genres=
            selected_genres,

        selected_languages=
            selected_languages

    )


# ============================================================
# MOVIE FILTER
# ============================================================

@app.route("/movies/filter")
def filter_movies():

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_genres = request.args.getlist(
        "genres"
    )

    selected_languages = request.args.getlist(
        "languages"
    )

    page = int(
        request.args.get(
            "page",
            1
        )
    )

    genre_ids = []

    for genre_name in selected_genres:

        for genre_id, name in GENRES.items():

            if name == genre_name:

                genre_ids.append(
                    genre_id
                )

                break

    language_map = {

        "bollywood": "hi",

        "korean": "ko",

        "anime": "ja",

        "hollywood": "en",

        "chinese": "zh",

        "spanish": "es",

        "french": "fr",

        "thai": "th"

    }

    language_code = None

    if selected_languages:

        language_code = language_map.get(
            selected_languages[0]
        )

    # --------------------------------------------------------
    # SEARCH MOVIES
    # --------------------------------------------------------

    if search:

        movies = search_tmdb_movies(
            search,
            page=page
        )

    # --------------------------------------------------------
    # FILTER MOVIES
    # --------------------------------------------------------

    else:

        movies = discover_movies(

            genres=(
                genre_ids
                if genre_ids
                else None
            ),

            language=language_code,

            page=page

        )

    return render_template(

        "movie_cards.html",

        movies=movies

    )


# ============================================================
# WATCH HISTORY
# ============================================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            SELECT movie_id, watched_at
            FROM history
            WHERE user_id = ?
            ORDER BY watched_at DESC
            """,

            (user_id,)

        )

        rows = cursor.fetchall()

    except sqlite3.Error as e:

        print(
            "History Fetch Error:",
            e
        )

        rows = []

    finally:

        connection.close()

    history_movies = []

    for row in rows:

        movie_id = row[
            "movie_id"
        ]

        try:

            movie = get_movie_details(
                movie_id
            )

            if movie:

                movie[
                    "watched_at"
                ] = row[
                    "watched_at"
                ]

                history_movies.append(
                    movie
                )

        except Exception as e:

            print(
                f"History movie error ({movie_id}):",
                e
            )

    return render_template(

        "history.html",

        history_movies=
            history_movies,

        active_page=
            "history"

    )


# ============================================================
# AI PICKS
# ============================================================

@app.route("/ai-picks")
def ai_picks():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session[
        "user_id"
    ]

    activity = get_user_activity(
        user_id
    )

    watchlist_ids = set(
        activity["watchlist"]
    )

    history_ids = set(
        activity["history"]
    )

    trailer_activity = (
        activity["trailer_activity"]
    )

    highly_interested_ids = set()

    interested_ids = set()

    for activity_item in trailer_activity:

        movie_id = activity_item[
            "movie_id"
        ]

        watch_percentage = float(

            activity_item.get(
                "watch_percentage",
                0
            ) or 0

        )

        if watch_percentage >= 100:

            highly_interested_ids.add(
                movie_id
            )

        elif watch_percentage >= 85:

            interested_ids.add(
                movie_id
            )

    # --------------------------------------------------------
    # NEW AI RECOMMENDATIONS
    # --------------------------------------------------------

    ai_movies = get_ai_recommendations(
        user_id
    )

    # --------------------------------------------------------
    # FINAL SAFETY FILTER
    # --------------------------------------------------------

    filtered_ai_movies = []

    for movie in ai_movies:

        movie_id = movie.get(
            "tmdb_id",
            movie.get("id")
        )

        if not movie_id:
            continue

        if movie_id in watchlist_ids:
            continue

        if movie_id in history_ids:
            continue

        filtered_ai_movies.append(
            movie
        )

        if len(
            filtered_ai_movies
        ) >= 10:

            break

    ai_movies = filtered_ai_movies

    return render_template(

        "ai_picks.html",

        ai_movies=ai_movies,

        watchlist_count=len(
            watchlist_ids
        ),

        history_count=len(
            history_ids
        ),

        interested_count=len(
            interested_ids
        ),

        highly_interested_count=len(
            highly_interested_ids
        ),

        selected_mood="",

        active_page=
            "ai_picks"

    )

@app.route("/track-mood", methods=["POST"])
def track_mood():

    if "user_id" not in session:
        return {"success": False}, 401

    user_id = session["user_id"]

    mood = request.json.get("mood", "").strip().lower()

    if not mood:
        return {"success": False}, 400

    connection = sqlite3.connect("movies.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO mood_activity (user_id, mood)
        VALUES (?, ?)
    """, (user_id, mood))

    connection.commit()
    connection.close()

    return {"success": True}


# ============================================================
# MOOD RESULTS
# ============================================================

@app.route("/mood-results")
def mood_results():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session[
        "user_id"
    ]

    selected_mood = request.args.get(
        "mood",
        ""
    ).strip().lower()

    refresh_seed = request.args.get(
        "refresh",
        ""
    )

    if not refresh_seed:

        refresh_seed = random.randint(
            1,
            999999999
        )

    else:

        try:

            refresh_seed = int(
                refresh_seed
            )

        except ValueError:

            refresh_seed = random.randint(
                1,
                999999999
            )

    mood_data = {

        "cozy": {

            "name":
                "Cozy & Chill",

            "description":
                "I just want to relax with a feel-good movie.",

            "icon":
                "◐"

        },

        "emotional": {

            "name":
                "Emotional Damage",

            "description":
                "Give me something that hits right in the feelings.",

            "icon":
                "♡"

        },

        "adrenaline": {

            "name":
                "Adrenaline Rush",

            "description":
                "Keep me on the edge of my seat.",

            "icon":
                "ϟ"

        },

        "mystery": {

            "name":
                "Make Me Guess",

            "description":
                "I want to solve the mystery before they do.",

            "icon":
                "◈"

        },

        "horror": {

            "name":
                "Give Me Nightmares",

            "description":
                "I'm voluntarily making bad decisions tonight.",

            "icon":
                "†"

        },

        "fantasy": {

            "name":
                "Escape Reality",

            "description":
                "Take me somewhere completely impossible.",

            "icon":
                "✦"

        },

        "romance": {

            "name":
                "Butterflies Please",

            "description":
                "I need romance. No questions asked.",

            "icon":
                "∞"

        },

        "mind": {

            "name":
                "Make Me Think",

            "description":
                "Give me something I'll think about tomorrow.",

            "icon":
                "◌"

        },

        "funny": {

            "name":
                "No Thoughts, Just Laughs",

            "description":
                "My brain is officially closed.",

            "icon":
                "°"

        },

        "explore": {

            "name":
                "Show Me Something New",

            "description":
                "Take me somewhere I've never been.",

            "icon":
                "◎"

        }

    }

    # --------------------------------------------------------
    # INVALID MOOD
    # --------------------------------------------------------

    if selected_mood not in mood_data:

        return redirect(
            url_for("ai_picks")
        )

    selected = mood_data[
        selected_mood
    ]

    # --------------------------------------------------------
    # USER ACTIVITY
    # --------------------------------------------------------

    activity = get_user_activity(
        user_id
    )

    watchlist_ids = set(
        activity["watchlist"]
    )

    history_ids = set(
        activity["history"]
    )

    trailer_activity_data = (
        activity["trailer_activity"]
    )

    # --------------------------------------------------------
    # ACTIVITY COUNTS
    # --------------------------------------------------------

    trailer_count = len(
        trailer_activity_data
    )

    highly_interested_count = sum(

        1

        for item
        in trailer_activity_data

        if float(
            item.get(
                "watch_percentage",
                0
            ) or 0
        ) >= 100

    )

    # --------------------------------------------------------
    # ENGAGED LANGUAGES
    # --------------------------------------------------------

    engaged_languages = (
        get_engaged_languages(
            user_id
        )
    )

    language_worlds = []

    for code in engaged_languages:

        info = LANGUAGE_INFO.get(
            code
        )

        if info:

            language_worlds.append({

                "code":
                    code,

                "name":
                    info["name"],

                "flag":
                    info["flag"]

            })

    language_worlds.sort(
        key=lambda item:
            item["name"]
    )

    # --------------------------------------------------------
    # PERSONALIZED MOVIES
    # --------------------------------------------------------

    mood_movies = (
        get_personalized_mood_movies(

            user_id,

            selected_mood,

            refresh_seed

        )
    )

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render_template(

        "mood_results.html",

        mood=
            selected_mood,

        mood_name=
            selected["name"],

        mood_description=
            selected["description"],

        mood_icon=
            selected["icon"],

        mood_movies=
            mood_movies,

        language_worlds=
            language_worlds,

        trailer_count=
            trailer_count,

        highly_interested_count=
            highly_interested_count,

        history_count=
            len(history_ids),

        watchlist_count=
            len(watchlist_ids),

        refresh_seed=
            refresh_seed,

        active_page=
            "ai_picks"

    )


# ============================================================
# TRAILER ACTIVITY
# ============================================================

@app.route(
    "/trailer-activity",
    methods=["POST"]
)
def trailer_activity():

    if "user_id" not in session:

        return {

            "success":
                False,

            "message":
                "Please login first."

        }, 401

    user_id = session[
        "user_id"
    ]

    data = request.get_json()

    if not data:

        return {

            "success":
                False,

            "message":
                "No trailer activity data received."

        }, 400

    movie_id = data.get(
        "movie_id"
    )

    watch_percentage = data.get(
        "watch_percentage",
        0
    )

    interest_level = data.get(
        "interest_level"
    )

    completed = data.get(
        "completed",
        0
    )

    if not movie_id:

        return {

            "success":
                False,

            "message":
                "Movie ID is required."

        }, 400

    try:

        watch_percentage = float(
            watch_percentage
        )

    except (
        TypeError,
        ValueError
    ):

        watch_percentage = 0

    watch_percentage = max(

        0,

        min(
            watch_percentage,
            100
        )

    )

    # --------------------------------------------------------
    # SERVER-SIDE INTEREST
    # --------------------------------------------------------

    if watch_percentage >= 100:

        interest_level = (
            "Highly Interested"
        )

        completed = 1

    elif watch_percentage >= 85:

        interest_level = (
            "Interested"
        )

        completed = 0

    else:

        interest_level = None

        completed = 0

    # --------------------------------------------------------
    # DON'T SAVE BELOW 85%
    # --------------------------------------------------------

    if watch_percentage < 85:

        return {

            "success":
                True,

            "recorded":
                False,

            "message":
                "Trailer watch percentage below interest threshold."

        }

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            INSERT INTO trailer_activity
            (
                user_id,
                movie_id,
                watch_percentage,
                interest_level,
                completed
            )
            VALUES (?, ?, ?, ?, ?)
            """,

            (

                user_id,

                movie_id,

                watch_percentage,

                interest_level,

                completed

            )

        )

        connection.commit()

        print("=" * 60)

        print(
            "TRAILER ACTIVITY SAVED"
        )

        print(
            "User ID:",
            user_id
        )

        print(
            "Movie ID:",
            movie_id
        )

        print(
            "Watch Percentage:",
            f"{watch_percentage:.1f}%"
        )

        print(
            "Interest Level:",
            interest_level
        )

        print(
            "Completed:",
            completed
        )

        print("=" * 60)

        return {

            "success":
                True,

            "recorded":
                True,

            "interest_level":
                interest_level,

            "watch_percentage":
                watch_percentage

        }

    except sqlite3.Error as e:

        connection.rollback()

        print(
            "Trailer Activity Error:",
            e
        )

        return {

            "success":
                False,

            "message":
                "Could not save movie activity."

        }, 500

    finally:

        connection.close()


# ============================================================
# MOVIE DETAILS
# ============================================================

@app.route(
    "/movie/<int:movie_id>"
)
def movie_details(movie_id):

    # ========================================================
    # RESOLVE LOCAL DATABASE ID → TMDB ID
    # ========================================================

    tmdb_movie_id = resolve_tmdb_movie_id(
        movie_id
    )

    print("=" * 60)

    print(
        "MOVIE DETAILS"
    )

    print(
        "URL ID:",
        movie_id
    )

    print(
        "TMDB ID:",
        tmdb_movie_id
    )

    print("=" * 60)

    # ========================================================
    # GET TMDB DETAILS
    # ========================================================

    movie = get_movie_details(
        tmdb_movie_id
    )

    # ========================================================
    # MORE LIKE THIS
    # ========================================================

    similar_movies = get_similar_movies(
        tmdb_movie_id
    )

    # --------------------------------------------------------
    # WATCHLIST STATUS
    # --------------------------------------------------------

    is_watchlisted = False

    # --------------------------------------------------------
    # WATCHED STATUS
    # --------------------------------------------------------

    is_watched = False

    if "user_id" in session:

        user_id = session[
            "user_id"
        ]

        connection = sqlite3.connect(
            DATABASE_NAME
        )

        cursor = connection.cursor()

        try:

            # ----------------------------------------------
            # WATCHLIST
            # ----------------------------------------------

            cursor.execute(

                """
                SELECT 1
                FROM watchlist
                WHERE user_id = ?
                AND movie_id = ?
                LIMIT 1
                """,

                (
                    user_id,
                    tmdb_movie_id
                )

            )

            if cursor.fetchone():

                is_watchlisted = True

            # ----------------------------------------------
            # HISTORY
            # ----------------------------------------------

            cursor.execute(

                """
                SELECT 1
                FROM history
                WHERE user_id = ?
                AND movie_id = ?
                LIMIT 1
                """,

                (
                    user_id,
                    tmdb_movie_id
                )

            )

            if cursor.fetchone():

                is_watched = True

        except sqlite3.Error as e:

            print(
                "Status Check Error:",
                e
            )

        finally:

            connection.close()

    return render_template(

        "movie.html",

        movie=movie,

        similar_movies=
            similar_movies,

        is_watchlisted=
            is_watchlisted,

        is_watched=
            is_watched

    )


# ============================================================
# ADD TO WATCHLIST
# ============================================================

@app.route(
    "/watchlist/add/<int:movie_id>",
    methods=["POST"]
)
def add_to_watchlist(movie_id):

    if "user_id" not in session:

        return {

            "success":
                False,

            "message":
                "Please login first."

        }, 401

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            INSERT INTO watchlist
            (user_id, movie_id)
            VALUES (?, ?)
            """,

            (
                user_id,
                movie_id
            )

        )

        connection.commit()

        return {

            "success":
                True,

            "watchlisted":
                True,

            "message":
                "❤️ Added to your Watchlist!"

        }

    except sqlite3.IntegrityError:

        return {

            "success":
                True,

            "watchlisted":
                True,

            "already_exists":
                True,

            "message":
                "❤️ This movie is already in your Watchlist."

        }

    except sqlite3.Error as e:

        print(
            "Watchlist Add Error:",
            e
        )

        return {

            "success":
                False,

            "message":
                "Could not add movie to Watchlist."

        }, 500

    finally:

        connection.close()


# ============================================================
# REMOVE FROM WATCHLIST
# ============================================================

@app.route(
    "/watchlist/remove/<int:movie_id>",
    methods=["POST"]
)
def remove_from_watchlist(movie_id):

    if "user_id" not in session:

        return {

            "success":
                False,

            "message":
                "Please login first."

        }, 401

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            DELETE FROM watchlist
            WHERE user_id = ?
            AND movie_id = ?
            """,

            (
                user_id,
                movie_id
            )

        )

        connection.commit()

        return {

            "success":
                True,

            "watchlisted":
                False,

            "message":
                "🗑️ Movie removed from your Watchlist."

        }

    except sqlite3.Error as e:

        print(
            "Watchlist Remove Error:",
            e
        )

        return {

            "success":
                False,

            "message":
                "Could not remove movie from Watchlist."

        }, 500

    finally:

        connection.close()


# ============================================================
# ADD TO HISTORY
# ============================================================

@app.route(
    "/history/add/<int:movie_id>",
    methods=["POST"]
)
def add_to_history(movie_id):

    if "user_id" not in session:

        return {

            "success":
                False,

            "message":
                "Please login first."

        }, 401

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            SELECT id
            FROM history
            WHERE user_id = ?
            AND movie_id = ?
            LIMIT 1
            """,

            (
                user_id,
                movie_id
            )

        )

        existing = cursor.fetchone()

        if existing:

            return {

                "success":
                    True,

                "watched":
                    True,

                "already_exists":
                    True,

                "message":
                    "✓ This movie is already in your Watch History."

            }

        cursor.execute(

            """
            INSERT INTO history
            (user_id, movie_id)
            VALUES (?, ?)
            """,

            (
                user_id,
                movie_id
            )

        )

        connection.commit()

        return {

            "success":
                True,

            "watched":
                True,

            "message":
                "✓ Added to your Watch History!"

        }

    except sqlite3.Error as e:

        print(
            "History Add Error:",
            e
        )

        return {

            "success":
                False,

            "message":
                "Could not add movie to Watch History."

        }, 500

    finally:

        connection.close()


# ============================================================
# REMOVE FROM HISTORY
# ============================================================

@app.route(
    "/history/remove/<int:movie_id>",
    methods=["POST"]
)
def remove_from_history(movie_id):

    if "user_id" not in session:

        return {

            "success":
                False,

            "message":
                "Please login first."

        }, 401

    user_id = session[
        "user_id"
    ]

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    try:

        cursor.execute(

            """
            DELETE FROM history
            WHERE user_id = ?
            AND movie_id = ?
            """,

            (
                user_id,
                movie_id
            )

        )

        connection.commit()

        return {

            "success":
                True,

            "watched":
                False,

            "message":
                "🗑️ Movie removed from Watch History."

        }

    except sqlite3.Error as e:

        print(
            "History Remove Error:",
            e
        )

        return {

            "success":
                False,

            "message":
                "Could not remove movie from Watch History."

        }, 500

    finally:

        connection.close()


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):

            flash(
                "Please fill in all fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        connection = sqlite3.connect(
            DATABASE_NAME
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            connection.close()

            flash(
                "An account with this email already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = (
            generate_password_hash(
                password
            )
        )

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        connection.commit()
        connection.close()

        flash(
            "Account created successfully! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(

                "login.html",

                error=
                    "Please enter your email and password."

            )

        connection = sqlite3.connect(
            DATABASE_NAME
        )

        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute(

            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,

            (email,)

        )

        user = cursor.fetchone()

        connection.close()

        if (

            user

            and

            check_password_hash(

                user[
                    "password_hash"
                ],

                password

            )

        ):

            session[
                "user_id"
            ] = user[
                "id"
            ]

            session[
                "user_name"
            ] = user[
                "name"
            ]

            session[
                "user_email"
            ] = user[
                "email"
            ]

            return redirect(
                url_for("home")
            )

        return render_template(

            "login.html",

            error=
                "Invalid email or password."

        )

    return render_template(
        "login.html"
    )

# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():
    return render_template("about.html")

# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout"
)
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )