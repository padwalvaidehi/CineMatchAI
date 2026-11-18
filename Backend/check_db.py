import sqlite3

conn = sqlite3.connect("movies.db")
cursor = conn.cursor()

# Get all tables
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""")

tables = cursor.fetchall()

print("\n========== TABLES ==========")

for table in tables:
    print("-", table[0])

print("\n========== COLUMNS ==========")

for table in tables:

    table_name = table[0]

    print("\nTABLE:", table_name)

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    for column in columns:
        print(
            "   ",
            column[1],
            "| TYPE:",
            column[2]
        )

conn.close()

print("\nDatabase check complete.")