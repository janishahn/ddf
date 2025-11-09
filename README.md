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

- **FastAPI** - Backend framework serving HTML and JSON endpoints
- **HTMX** - Frontend interactivity without full page reloads
- **Jinja2** - Server-side templating
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
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload

# Visit http://localhost:8000
```

## Project Structure

- `main.py` - FastAPI application and routes
- `models.py` - Pydantic data models
- `cache.py` - Disk and in-memory caching
- `itunes_client.py` - iTunes API client
- `catalog.py` - Album catalog building and bucketing
- `analytics.py` - Usage analytics tracking
- `cookies.py` - Cookie management helpers
- `templates/` - Jinja2 templates
- `static/` - Static assets (CSS)
- `cache/` - Cached data (artist ID, albums, buckets, lengths, analytics)