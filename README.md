# fastapi_at1

A lightweight FastAPI web app for saving movie ratings, viewing statistics, and generating AI-powered movie recommendations.
Dependencies are managed with Poetry.

### Project Structure

```

.
├── src
│   ├── templates
│   │   ├── movie_detail.html
│   │   ├── recommend.html
│   │   ├── index.html
│   │   └── search_results.html
│   ├── main.py
│   ├── services
│   │   ├── api.py
│   │   ├── database.py
│   │   └── page.py
│   └── static
│       └── placeholder.md
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── poetry.lock
├── pyproject.toml
└── tests
    └── test_main.py
```

### Features

Add/search movies using TMDB

Rate, update, and remove saved movies

Statistics page (average rating, year metrics, distribution)

AI recommendation page powered by OpenAI

Tailwind-based UI, SQLite storage

### Setup & Run

1. Install dependencies
`poetry install`

2. Create a .env file

```
TMDB_API_KEY=your_tmdb_key
OPENAI_API_KEY=your_openai_key
```

3. Run the server
`poetry run uvicorn main:app --reload`

App will be available at:

<http://127.0.0.1:8000/>

### License

MIT (see LICENSE)
