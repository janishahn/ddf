# Environment

Environment variables, external dependencies, and setup notes.

## What belongs here

Required env vars, external API keys/services, dependency quirks, platform-specific notes.

## What does NOT belong here

Service ports/commands (use `.factory/services.yaml`).

---

## Backend (FastAPI)

- **Runtime:** Python 3.12+ with uv package manager
- **Port:** 8000 (configurable)
- **Dependencies:** FastAPI, uvicorn, httpx, pydantic

## Frontend (Vite + React)

- **Runtime:** Node.js with npm
- **Port:** 3000 (Vite dev server)
- **Build:** Production build outputs to `frontend/dist/`
- **Proxy:** Vite proxies `/api` requests to `http://127.0.0.1:8000`

## Dependencies

- iTunes API (external, no auth required)
- No database required (uses file-based cache in `cache/` directory)

## Notes

- Run backend first, then frontend (frontend proxies to backend)
- The `start.sh` script uses port 8005 but mission uses port 8000 for consistency with Vite proxy config
