import sqlite3

from database import DATABASE_NAME


connection = sqlite3.connect(DATABASE_NAME)

cursor = connection.cursor()


print("\n========== DATABASE SUMMARY ==========\n")


# USERS

cursor.execute(
    "SELECT COUNT(*) FROM users"
)

print(
    "Total Users:",
    cursor.fetchone()[0]
)


# MOVIES

cursor.execute(
    "SELECT COUNT(*) FROM movies"
)

print(
    "Total Movies:",
    cursor.fetchone()[0]
)


# WATCHLIST

cursor.execute(
    "SELECT COUNT(*) FROM watchlist"
)

print(
    "Total Watchlist Entries:",
    cursor.fetchone()[0]
)


# HISTORY

cursor.execute(
    "SELECT COUNT(*) FROM history"
)

print(
    "Total Watch History:",
    cursor.fetchone()[0]
)


# TRAILER ACTIVITY

cursor.execute(
    "SELECT COUNT(*) FROM trailer_activity"
)

print(
    "Total Trailer Activities:",
    cursor.fetchone()[0]
)


connection.close()


print("\n======================================")
print("Database verification complete!")