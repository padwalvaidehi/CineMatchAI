import sqlite3
import pandas as pd
import os

# ============================================
# DATABASE
# ============================================

DATABASE_NAME = "movies.db"


# ============================================
# CREATE OUTPUT FOLDER
# ============================================

OUTPUT_FOLDER = "powerbi_data"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================
# CONNECT TO DATABASE
# ============================================

connection = sqlite3.connect(
    DATABASE_NAME
)


# ============================================
# TABLES TO EXPORT
# ============================================

tables = [

    "users",

    "movies",

    "watchlist",

    "history",

    "trailer_activity"

]


# ============================================
# EXPORT TABLES
# ============================================

for table in tables:

    print(
        f"Exporting {table}..."
    )

    dataframe = pd.read_sql_query(

        f"SELECT * FROM {table}",

        connection

    )

    file_path = os.path.join(

        OUTPUT_FOLDER,

        f"{table}.csv"

    )

    dataframe.to_csv(

        file_path,

        index=False

    )

    print(

        f"{table}.csv exported successfully!"

    )


# ============================================
# CLOSE DATABASE
# ============================================

connection.close()


print(
    "\n================================="
)

print(
    "Power BI data export complete!"
)

print(
    "================================="
)