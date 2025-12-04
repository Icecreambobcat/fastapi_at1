import logging
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
from dotenv import load_dotenv
from openai import OpenAI

# TODO: Local module imports
from services.database import (
    Movie,
    init_db,
    get_all_movies,
    get_movie_by_id,
    add_movie_to_db,
    drop_movie_from_db,
    update_movie_rating,
    get_review_stats,
)

# NOTE: SECTION: setup
app = FastAPI(
    title="placeholder",
    description="placeholder",
    version="0.1.0",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Application starting up...")

app = FastAPI()
init_db()  # Initialize database at startup - This will be handled by tests or explicit startup event
logging.info(
    "Database initialization will be handled by tests or explicit startup event."
)

load_dotenv()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError(
        "TMDB_API_KEY not found in environment variables. Please set it in your .env file or environment."
    )
TMDB_BASE_URL = "https://api.themoviedb.org/3"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please set it in your .env file or environment."
    )
client = OpenAI(api_key=OPENAI_API_KEY)


# NOTE: SECTION: routes
@app.get("/")
async def root(request: Request):
    movies = get_all_movies()
    return templates.TemplateResponse(
        "index.html", {"request": request, "movies": movies}
    )


@app.get("/recommend")
async def recommend_page(request: Request):
    return templates.TemplateResponse(
        "recommend.html",
        {"request": request, "recommendations": None, "loading": False},
    )


@app.post("/recommend/generate")
async def recommend_generate(request: Request):
    movies = get_all_movies()
    stats = get_review_stats()

    # Prepare compact input summary
    movie_list_text = "\n".join(
        [f"- {m.title} ({m.year}) — rated {m.rating}/5" for m in movies]
    )

    stats_text = (
        f"Total movies: {stats['total']}\n"
        f"Average rating: {stats['avg_rating']}\n"
        f"Average year: {stats['avg_year']}\n"
        f"Most common year: {stats['most_common_year']}\n"
        f"Rating distribution: {stats['distribution']}"
    )

    prompt = f"""
You are an expert movie curator AI.
Using the user's movie database and statistics, produce 3–5 personalised movie recommendations.

Database movies:
{movie_list_text}

Stats:
{stats_text}

Respond in clean bullet points with:
- Movie title
- Year
- Why it fits the user's tastes
- No extra explanations
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful movie recommendation AI.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        ai_text = response.choices[0].message.content

    except Exception as e:
        ai_text = f"Error generating recommendations: {str(e)}"

    return templates.TemplateResponse(
        "recommend.html",
        {"request": request, "recommendations": ai_text, "loading": False},
    )


@app.get("/movie/{movie_id}")
async def movie_detail(request: Request, movie_id: int):
    """Display detailed view of a single movie."""
    movie = get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return templates.TemplateResponse(
        "movie_detail.html", {"request": request, "movie": movie}
    )


@app.get("/stats")
async def stats_page(request: Request):
    stats = get_review_stats()
    return templates.TemplateResponse(
        "stats.html", {"request": request, "stats": stats}
    )


@app.get("/search")
async def search(request: Request, query: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/search/movie",
                params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "language": "en-US",
                    "page": 1,
                },
            )
            response.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)

            response_data = response.json()
            if "results" not in response_data or not isinstance(
                response_data["results"], list
            ):
                logging.error(
                    f"Unexpected response format from TMDb for query '{query}': 'results' key missing or not a list."
                )
                raise HTTPException(
                    status_code=500, detail="Unexpected response format from TMDb."
                )

            results = response_data["results"]
            movies = [
                Movie(
                    id=movie["id"],
                    title=movie["title"],
                    year=(
                        movie["release_date"][:4] if movie.get("release_date") else None
                    ),
                    poster_path=(
                        f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                        if movie.get("poster_path")
                        else None
                    ),
                )
                for movie in results[:5]  # Limit to 5 results
            ]

        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "movies": movies, "query": query},
        )
    except httpx.RequestError as e:
        logging.error(f"TMDb API request error for query '{query}': {e}")
        raise HTTPException(
            status_code=503, detail="Could not connect to the movie service."
        )
    except httpx.HTTPStatusError as e:
        logging.error(
            f"TMDb API error for query '{query}': Status {e.response.status_code}"
        )
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Failed to fetch movies from TMDb.",
        )


@app.post("/add-movie")
async def add_movie(
    movie_id: int = Form(...),
    rating: int = Form(...),
):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/{movie_id}",
                params={"api_key": TMDB_API_KEY, "language": "en-US"},
                timeout=10,
            )
            response.raise_for_status()
            response_data = response.json()
            title = response_data["title"]
            year = (
                response_data["release_date"][:4]
                if response_data.get("release_date")
                else None
            )
            poster_path = (
                f"https://image.tmdb.org/t/p/w500{response_data['poster_path']}"
                if response_data.get("poster_path")
                else None
            )
            assert isinstance(title, str)
            assert isinstance(year, (str))
            assert isinstance(poster_path, (str))
            # ensure proper data form

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        add_movie_to_db(movie_id, title, year, poster_path, rating)
        logging.info(f"Movie '{title}' (ID: {movie_id}) added with rating: {rating}.")
    return RedirectResponse(url="/", status_code=303)


@app.post("/remove-movie")
async def remove_movie(movie_id: int = Form(...)):
    drop_movie_from_db(movie_id)
    logging.info(f"Movie with ID: {movie_id}) removed.")
    return RedirectResponse(url="/", status_code=303)


@app.post("/update-rating")
async def update_rating(movie_id: int = Form(...), rating: int = Form(...)):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    update_movie_rating(movie_id, rating)
    logging.info(f"Movie with ID: {movie_id}) updated with rating: {rating}.")
    return RedirectResponse(url="/", status_code=303)


# NOTE: SECTION: boilerplate run code
def main() -> None:
    import uvicorn

    uvicorn.run(app)


if __name__ == "__main__":
    main()
