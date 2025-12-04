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
