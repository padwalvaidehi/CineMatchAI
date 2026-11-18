import sqlite3
import random
from datetime import datetime, timedelta


DATABASE_NAME = "movies.db"


# ------------------------------------------
# DATABASE CONNECTION
# ------------------------------------------

connection = sqlite3.connect(DATABASE_NAME)

cursor = connection.cursor()


# ------------------------------------------
# GET ALL USERS
# ------------------------------------------

cursor.execute("""
    SELECT id
    FROM users
""")

users = cursor.fetchall()

user_ids = [
    user[0]
    for user in users
]


# ------------------------------------------
# GET EXISTING MOVIES
# ------------------------------------------

cursor.execute("""
    SELECT tmdb_id
    FROM movies
    WHERE tmdb_id IS NOT NULL
""")

movies = cursor.fetchall()

movie_ids = [
    movie[0]
    for movie in movies
]


print(f"Total users found: {len(user_ids)}")
print(f"Total movies found: {len(movie_ids)}")


# ------------------------------------------
# SAFETY CHECK
# ------------------------------------------

if not movie_ids:

    print("No movies found!")

    connection.close()

    exit()


# ------------------------------------------
# GENERATE TRAILER ACTIVITY
# ------------------------------------------

trailer_entries = 0


for user_id in user_ids:


    # --------------------------------------
    # DIFFERENT USER ACTIVITY LEVELS
    # --------------------------------------

    number_of_trailers = random.choices(

        population=[
            0,
            1,
            2,
            3,
            5,
            7,
            10,
            15,
            20
        ],

        weights=[
            5,
            8,
            12,
            18,
            20,
            16,
            11,
            7,
            3
        ]

    )[0]


    number_of_trailers = min(
        number_of_trailers,
        len(movie_ids)
    )


    # --------------------------------------
    # SELECT MOVIES
    # --------------------------------------

    selected_movies = random.sample(

        movie_ids,

        number_of_trailers

    )


    # --------------------------------------
    # GENERATE ACTIVITY
    # --------------------------------------

    for movie_id in selected_movies:


        # ----------------------------------
        # WATCH PERCENTAGE
        # ----------------------------------

        watch_percentage = round(

            random.choices(

                population=[

                    random.uniform(10, 30),

                    random.uniform(30, 60),

                    random.uniform(60, 85),

                    random.uniform(85, 100)

                ],

                weights=[

                    15,
                    25,
                    30,
                    30

                ]

            )[0],

            2

        )


        # ----------------------------------
        # TRAILER DURATION
        # Assume average trailer
        # is around 150 seconds
        # ----------------------------------

        trailer_length = random.randint(
            120,
            180
        )


        watch_duration = round(

            (
                trailer_length
                * watch_percentage
            )
            / 100,

            2

        )


        # ----------------------------------
        # INTEREST LEVEL
        # ----------------------------------

        if watch_percentage >= 90:

            interest_level = "High"


        elif watch_percentage >= 60:

            interest_level = "Medium"


        else:

            interest_level = "Low"


        # ----------------------------------
        # COMPLETED
        # ----------------------------------

        if watch_percentage >= 95:

            completed = 1

        else:

            completed = 0


        # ----------------------------------
        # RANDOM DATE
        # ----------------------------------

        days_ago = random.randint(
            0,
            365
        )


        started_at = (

            datetime.now()

            - timedelta(
                days=days_ago
            )

        )


        # ----------------------------------
        # INSERT DATA
        # ----------------------------------

        cursor.execute(

            """
            INSERT INTO trailer_activity (

                user_id,
                movie_id,
                started_at,
                watch_duration,
                watch_percentage,
                interest_level,
                completed

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,

            (

                user_id,

                movie_id,

                started_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                watch_duration,

                watch_percentage,

                interest_level,

                completed

            )

        )


        trailer_entries += 1


# ------------------------------------------
# SAVE DATA
# ------------------------------------------

connection.commit()

connection.close()


print()

print(
    f"{trailer_entries} trailer activity entries generated successfully!"
)

print(
    "Trailer activity generation complete."
)

# ============================================================
# GENERATE DUMMY MOOD ACTIVITY
# ============================================================

import sqlite3
import random
from datetime import datetime, timedelta

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

moods = [
    "cozy",
    "emotional",
    "adrenaline",
    "mystery",
    "horror",
    "fantasy",
    "romance",
    "mind",
    "funny",
    "explore"
]

cursor.execute("SELECT id FROM users")
users = cursor.fetchall()

for (user_id,) in users:

    number_of_selections = random.randint(2, 8)

    for _ in range(number_of_selections):

        mood = random.choice(moods)

        selected_at = datetime.now() - timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        cursor.execute("""
            INSERT INTO mood_activity
            (user_id, mood, selected_at)
            VALUES (?, ?, ?)
        """, (
            user_id,
            mood,
            selected_at
        ))

connection.commit()
connection.close()

print("Dummy mood activity generated successfully!")