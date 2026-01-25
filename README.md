# Die drei ??? Album Viewer

A FastAPI application that displays random album covers from the "Die drei ???" series with age-based filtering.

## Features

- Shows a random *Die drei ???* album cover centered on the page
- Includes caption with year, title, and Apple Music link
- "Reroll" button to fetch a new random album without page reload
- Age filter with four options: Old · Medium · New · All
- Cookie-based persistence for last selected age filter (90 days)
- Optional total runtime display when available

## Architecture

- **FastAPI** - JSON API and static SPA hosting
- **React + Vite** - Single-page app frontend
- **shadcn/ui + Radix UI** - UI primitives
- **Tailwind CSS** - Styling
- **iTunes API** - Album data source

## How It Works

1. The application fetches the complete "Die drei ???" album catalog from iTunes API on startup
2. Albums are sorted and split into three age-based buckets: Old, Medium, New
3. The current album is displayed with the option to reroll or filter by age
4. User's age preference is persisted in a cookie

## Local Development

```bash
# Install dependencies
uv sync

# Run the backend
uvicorn main:app --reload

# In another terminal, run the frontend
cd frontend
npm run dev

# Visit http://localhost:8000
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Production

```bash
# Build the frontend
cd frontend
npm run build

# Run the backend + static SPA
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

- `main.py` - FastAPI application and routes
- `models.py` - Pydantic data models
- `cache.py` - Disk and in-memory caching
- `itunes_client.py` - iTunes API client
- `catalog.py` - Album catalog building and bucketing
- `analytics.py` - Usage analytics tracking
- `cookies.py` - Cookie management helpers
- `frontend/` - Vite React SPA
- `cache/` - Cached data (artist ID, albums, buckets, lengths, analytics)
