import sqlite3
from typing import List, Optional
from pydantic import BaseModel

DATABASE_NAME = "movies.db"


class Movie(BaseModel):
    id: int
    title: str
    year: Optional[str] = None
    poster_path: Optional[str] = None
    rating: Optional[int] = None


def init_db(conn=None):  # Allow passing a connection
    supplied_conn = bool(conn)
    if not conn:
        conn = sqlite3.connect(DATABASE_NAME)

    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS movies
            (id INTEGER PRIMARY KEY,
             title TEXT NOT NULL,
             year TEXT,
             poster_path TEXT,
             rating INTEGER NOT NULL)
        """
        )
        conn.commit()
    finally:
        if not supplied_conn and conn:  # If we opened it, we close it
            conn.close()


def get_all_movies() -> List[Movie]:
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM movies")
        movies = [
            Movie(
                id=row[0], title=row[1], year=row[2], poster_path=row[3], rating=row[4]
            )
            for row in c.fetchall()
        ]
        return movies


def get_movie_by_id(movie_id: int) -> Optional[Movie]:
    """Get a single movie by its ID from the database."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
        row = c.fetchone()
        if row:
            return Movie(
                id=row[0], title=row[1], year=row[2], poster_path=row[3], rating=row[4]
            )
        return None


def add_movie_to_db(
    movie_id: int, title: str, year: str, poster_path: str, rating: int
):
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO movies (id, title, year, poster_path, rating) VALUES (?, ?, ?, ?, ?)",
            (movie_id, title, year, poster_path, rating),
        )
        conn.commit()


def drop_movie_from_db(movie_id: int):
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        conn.commit()


def update_movie_rating(movie_id: int, rating: int):
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE movies SET rating = ? WHERE id = ?", (rating, movie_id))
        conn.commit()


def get_review_stats():
    """Return stats about movies in the DB."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        c = conn.cursor()

        # Total
        c.execute("SELECT COUNT(*) FROM movies")
        total = c.fetchone()[0]

        # Average rating
        c.execute("SELECT AVG(rating) FROM movies")
        avg_rating = c.fetchone()[0]
        avg_rating = round(avg_rating, 2) if avg_rating else None

        # Rating distribution
        c.execute(
            """
            SELECT rating, COUNT(*)
            FROM movies
            GROUP BY rating
            ORDER BY rating
        """
        )
        distribution = {row[0]: row[1] for row in c.fetchall()}

        # Average year (filter out NULL or blank)
        c.execute(
            """
            SELECT AVG(CAST(year AS INTEGER))
            FROM movies
            WHERE year IS NOT NULL AND TRIM(year) != ''
        """
        )
        avg_year = c.fetchone()[0]
        avg_year = int(avg_year) if avg_year else None

        # Most common year
        c.execute(
            """
            SELECT year, COUNT(*)
            FROM movies
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY COUNT(*) DESC, year ASC
            LIMIT 1
        """
        )
        row = c.fetchone()
        most_common_year = row[0] if row else None

    return {
        "total": total,
        "avg_rating": avg_rating,
        "distribution": distribution,
        "avg_year": avg_year,
        "most_common_year": most_common_year,
    }
