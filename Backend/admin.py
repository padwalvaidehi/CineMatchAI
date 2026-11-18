from flask import Flask, Blueprint, render_template, redirect, url_for, session, request
import sqlite3
import webbrowser
from werkzeug.security import check_password_hash
from database import DATABASE_NAME

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = sqlite3.connect(DATABASE_NAME)
        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email, password_hash
            FROM admins
            WHERE email = ?
            """,
            (email,)
        )

        admin = cursor.fetchone()

        connection.close()

        if admin and check_password_hash(
            admin["password_hash"],
            password
        ):

            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]
            session["admin_email"] = admin["email"]

            return redirect(
    url_for("admin.admin_dashboard")
)

        return render_template(
            "admin/admin_login.html",
            error="Invalid email or password."
        )

    return render_template(
        "admin/admin_login.html"
    )

@admin_bp.route("/ai")
def admin_ai():

    # --------------------------------------------------------
    # ADMIN LOGIN REQUIRED
    # --------------------------------------------------------

    if "admin_id" not in session:
        return redirect(
            url_for("admin.admin_login")
        )

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    # --------------------------------------------------------
    # MOST WATCHED MOVIE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            m.title,
            COUNT(h.id) AS count
        FROM history h
        LEFT JOIN movies m
            ON h.movie_id = m.tmdb_id
        GROUP BY h.movie_id
        ORDER BY count DESC
        LIMIT 1
    """)

    most_watched_movie = cursor.fetchone()


    # --------------------------------------------------------
    # MOST WATCHLISTED MOVIE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            m.title,
            COUNT(w.id) AS count
        FROM watchlist w
        LEFT JOIN movies m
            ON w.movie_id = m.tmdb_id
        GROUP BY w.movie_id
        ORDER BY count DESC
        LIMIT 1
    """)

    most_watchlisted_movie = cursor.fetchone()


    # --------------------------------------------------------
    # MOST SELECTED MOOD
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            mood,
            COUNT(*) AS count
        FROM mood_activity
        GROUP BY mood
        ORDER BY count DESC
        LIMIT 1
    """)

    most_selected_mood = cursor.fetchone()


    # --------------------------------------------------------
    # TOTAL MOOD SELECTIONS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM mood_activity
    """)

    total_mood_selections = (
        cursor.fetchone()["count"]
    )


    # --------------------------------------------------------
    # MOST ENGAGED USERS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            u.name,
            u.email,

            (
                COALESCE(t.trailer_count, 0)
                +
                COALESCE(h.history_count, 0)
                +
                COALESCE(w.watchlist_count, 0)
                +
                COALESCE(m.mood_count, 0)
            ) AS activity_count

        FROM users u

        LEFT JOIN (
            SELECT
                user_id,
                COUNT(*) AS trailer_count
            FROM trailer_activity
            GROUP BY user_id
        ) t
            ON u.id = t.user_id

        LEFT JOIN (
            SELECT
                user_id,
                COUNT(*) AS history_count
            FROM history
            GROUP BY user_id
        ) h
            ON u.id = h.user_id

        LEFT JOIN (
            SELECT
                user_id,
                COUNT(*) AS watchlist_count
            FROM watchlist
            GROUP BY user_id
        ) w
            ON u.id = w.user_id

        LEFT JOIN (
            SELECT
                user_id,
                COUNT(*) AS mood_count
            FROM mood_activity
            GROUP BY user_id
        ) m
            ON u.id = m.user_id

        ORDER BY activity_count DESC

        LIMIT 5
    """)

    active_users = cursor.fetchall()


    # --------------------------------------------------------
    # CLOSE DATABASE
    # --------------------------------------------------------

    connection.close()


    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render_template(

        "admin/admin_ai.html",

        most_watched_movie=
            most_watched_movie,

        most_watchlisted_movie=
            most_watchlisted_movie,

        most_selected_mood=
            most_selected_mood,

        total_mood_selections=
            total_mood_selections,

        active_users=
            active_users,

        active_page=
            "admin_ai"

    )


@admin_bp.route("/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin.admin_login")
    )

@admin_bp.route("/settings")
def admin_settings():

    if "admin_id" not in session:

        return redirect(
            url_for("admin.admin_login")
        )


    return render_template(

        "admin/admin_settings.html",

        active_page="admin_settings"

    )

@admin_bp.route("/dashboard")
def admin_dashboard():

    if "admin_id" not in session:

        return redirect(
            url_for("admin.admin_login")
        )

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM movies
        """
    )

    total_movies = cursor.fetchone()["count"]


    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        """
    )

    total_users = cursor.fetchone()["count"]


    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM watchlist
        """
    )

    total_watchlist = cursor.fetchone()["count"]


    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM history
        """
    )

    total_history = cursor.fetchone()["count"]


    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM trailer_activity
        """
    )

    total_trailer_activity = cursor.fetchone()["count"]


    connection.close()


    return render_template(

        "admin/admin_dashboard.html",

        total_movies=total_movies,

        total_users=total_users,

        total_watchlist=total_watchlist,

        total_history=total_history,

        total_trailer_activity=total_trailer_activity,

        active_page="admin_dashboard"

    )



@admin_bp.route("/users")
def admin_users():

    # ============================================
    # ADMIN LOGIN REQUIRED
    # ============================================

    if "admin_id" not in session:

        return redirect(
            url_for("admin.admin_login")
        )


    # ============================================
    # GET SEARCH VALUE
    # ============================================

    search = request.args.get(
        "search",
        ""
    ).strip()


    # ============================================
    # DATABASE CONNECTION
    # ============================================

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    # ============================================
    # GET USERS
    # ============================================

    if search:

        cursor.execute(
            """
            SELECT

                u.id,
                u.name,
                u.email,
                u.created_at,

                COUNT(DISTINCT w.id)
                    AS watchlist_count,

                COUNT(DISTINCT h.id)
                    AS history_count,

                COUNT(DISTINCT t.id)
                    AS trailer_count

            FROM users u

            LEFT JOIN watchlist w
                ON u.id = w.user_id

            LEFT JOIN history h
                ON u.id = h.user_id

            LEFT JOIN trailer_activity t
                ON u.id = t.user_id

            WHERE

                u.name LIKE ?

                OR

                u.email LIKE ?

            GROUP BY u.id

            ORDER BY u.created_at DESC
            """,
            (
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:

        cursor.execute(
            """
            SELECT

                u.id,
                u.name,
                u.email,
                u.created_at,

                COUNT(DISTINCT w.id)
                    AS watchlist_count,

                COUNT(DISTINCT h.id)
                    AS history_count,

                COUNT(DISTINCT t.id)
                    AS trailer_count

            FROM users u

            LEFT JOIN watchlist w
                ON u.id = w.user_id

            LEFT JOIN history h
                ON u.id = h.user_id

            LEFT JOIN trailer_activity t
                ON u.id = t.user_id

            GROUP BY u.id

            ORDER BY u.created_at DESC
            """
        )


    users = cursor.fetchall()

    connection.close()


    # ============================================
    # RENDER PAGE
    # ============================================

    return render_template(

        "admin/admin_users.html",

        users=users,

        search=search,

        active_page="admin_users"

    )
@admin_bp.route("/analytics")
def admin_analytics():

    if "admin_id" not in session:

        return redirect(
            url_for("admin.admin_login")
        )


    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    # ---------------------------------------------
    # TOTAL MOVIES
    # ---------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM movies"
    )

    total_movies = cursor.fetchone()[0]


    # ---------------------------------------------
    # TOTAL USERS
    # ---------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]


    # ---------------------------------------------
    # TOTAL WATCHLIST ENTRIES
    # ---------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM watchlist"
    )

    total_watchlist = cursor.fetchone()[0]


    # ---------------------------------------------
    # TOTAL WATCH HISTORY
    # ---------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM history"
    )

    total_history = cursor.fetchone()[0]


    # ---------------------------------------------
    # TOTAL TRAILER ACTIVITY
    # ---------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM trailer_activity"
    )

    total_trailer_activity = cursor.fetchone()[0]


    # ---------------------------------------------
    # MOVIES BY LANGUAGE
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT
            language,
            COUNT(*) AS count

        FROM movies

        WHERE language IS NOT NULL
        AND language != ''

        GROUP BY language

        ORDER BY count DESC

        LIMIT 10
        """
    )

    languages = cursor.fetchall()


    # ---------------------------------------------
    # MOST WATCHLISTED MOVIES
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT
            m.title,
            COUNT(w.id) AS count

        FROM watchlist w

        LEFT JOIN movies m
        ON w.movie_id = m.tmdb_id

        GROUP BY w.movie_id

        ORDER BY count DESC

        LIMIT 5
        """
    )

    top_watchlisted = cursor.fetchall()


    # ---------------------------------------------
    # MOST WATCHED MOVIES
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT
            m.title,
            COUNT(h.id) AS count

        FROM history h

        LEFT JOIN movies m
        ON h.movie_id = m.tmdb_id

        GROUP BY h.movie_id

        ORDER BY count DESC

        LIMIT 5
        """
    )

    top_watched = cursor.fetchall()

        # ---------------------------------------------
    # MOOD ANALYTICS
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT
            mood,
            COUNT(*) AS count

        FROM mood_activity

        GROUP BY mood

        ORDER BY count DESC
        """
    )

    mood_distribution = cursor.fetchall()


    # ---------------------------------------------
    # MOST SELECTED MOOD
    # ---------------------------------------------

    most_selected_mood = (
        mood_distribution[0]["mood"]
        if mood_distribution
        else None
    )

    most_selected_mood_count = (
        mood_distribution[0]["count"]
        if mood_distribution
        else 0
    )


    connection.close()


    return render_template(

        "admin/admin_analytics.html",

        total_movies=total_movies,

        total_users=total_users,

        total_watchlist=total_watchlist,

        total_history=total_history,

        total_trailer_activity=total_trailer_activity,

        languages=languages,

        top_watchlisted=top_watchlisted,

        mood_distribution=mood_distribution,

        most_selected_mood=most_selected_mood,

        most_selected_mood_count=most_selected_mood_count,

        top_watched=top_watched,

        active_page="admin_analytics"

    )

# ============================================================
# ADMIN WATCH HISTORY
# ============================================================

@admin_bp.route("/watch-history")
def admin_watch_history():

    # ============================================
    # ADMIN LOGIN REQUIRED
    # ============================================

    if "admin_id" not in session:

        return redirect(
            url_for("admin.admin_login")
        )

    # ============================================
    # DATABASE CONNECTION
    # ============================================

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    # ============================================
    # GET WATCH HISTORY
    # ============================================

    cursor.execute(
        """
        SELECT
            h.id,
            u.name AS user_name,
            u.email AS user_email,
            m.title AS movie_title,
            h.watched_at

        FROM history h

        LEFT JOIN users u
            ON h.user_id = u.id

        LEFT JOIN movies m
            ON h.movie_id = m.tmdb_id

        ORDER BY h.watched_at DESC
        """
    )

    watch_history = cursor.fetchall()

    connection.close()

    # ============================================
    # RENDER PAGE
    # ============================================

    return render_template(
        "admin/admin_watch_history.html",

        watch_history=watch_history,

        active_page="admin_watch_history"
    )

# ============================================================
# ADMIN TRAILER ANALYTICS
# ============================================================

@admin_bp.route("/trailer-analytics")
def admin_trailer_analytics():

    if "admin_id" not in session:
        return redirect(
            url_for("admin.admin_login")
        )

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    # ========================================================
    # TOTAL TRAILER ACTIVITIES
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM trailer_activity
        """
    )

    total_trailers = cursor.fetchone()["count"]


    # ========================================================
    # COMPLETED TRAILERS
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM trailer_activity
        WHERE completed = 1
        """
    )

    completed_trailers = cursor.fetchone()["count"]


    # ========================================================
    # AVERAGE COMPLETION PERCENTAGE
    # ========================================================

    cursor.execute(
        """
        SELECT AVG(watch_percentage) AS average
        FROM trailer_activity
        """
    )

    average_completion = (
        cursor.fetchone()["average"] or 0
    )


    # ========================================================
    # INTEREST DISTRIBUTION
    # ========================================================

    cursor.execute(
        """
        SELECT
            interest_level,
            COUNT(*) AS count
        FROM trailer_activity
        GROUP BY interest_level
        ORDER BY count DESC
        """
    )

    interest_levels = cursor.fetchall()


    # ========================================================
    # MOST ACTIVE TRAILER USERS
    # ========================================================

    cursor.execute(
        """
        SELECT
            u.name,
            u.email,
            COUNT(t.id) AS activity_count
        FROM trailer_activity t

        LEFT JOIN users u
            ON t.user_id = u.id

        GROUP BY t.user_id

        ORDER BY activity_count DESC

        LIMIT 10
        """
    )

    active_users = cursor.fetchall()


    # ========================================================
    # USER TRAILER ACTIVITY DETAILS
    # ========================================================

    cursor.execute(
    """
    SELECT
        u.name,
        u.email,
        m.title,
        t.watch_percentage,
        t.interest_level,
        t.completed

    FROM trailer_activity t

    LEFT JOIN users u
        ON t.user_id = u.id

    LEFT JOIN movies m
        ON t.movie_id = m.tmdb_id

    ORDER BY t.watch_percentage DESC
    """
)

    trailer_activity_details = cursor.fetchall()


    connection.close()


    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "admin/admin_trailer_analytics.html",

        total_trailer_activity=total_trailers,

        completed_trailers=completed_trailers,

        average_completion=round(
            average_completion, 2
        ),

        interest_levels=interest_levels,

        active_users=active_users,

        trailer_activity_details=
            trailer_activity_details,

        active_page="admin_trailer_analytics"
    )

# ============================================================
# RUN ADMIN APPLICATION SEPARATELY
# ============================================================

if __name__ == "__main__":

    app = Flask(__name__)

    app.secret_key = "cinematchai-secret-key"
    app.config["SESSION_COOKIE_NAME"] = "admin_session"

    app.register_blueprint(admin_bp)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    webbrowser.register(
    "chrome",
    None,
    webbrowser.BackgroundBrowser(chrome_path)
)

    webbrowser.get("chrome").open(
    "http://127.0.0.1:5001/admin/login"
)

    app.run(
        debug=True,
        port=5001
    )