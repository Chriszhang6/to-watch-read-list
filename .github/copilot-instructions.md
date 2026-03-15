# Copilot Instructions for To Watch/Read List

## Project Overview

A personal link collection tool (FastAPI + SQLAlchemy) that automatically extracts metadata from YouTube videos and web pages. Features user authentication, password reset via email, and responsive UI with Alpine.js.

## Build, Test & Development Commands

### Prerequisites
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with hot reload
uvicorn app.main:app --reload

# With explicit host/port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_auth.py

# Run with coverage report
pytest --cov=app

# Run specific test function
pytest tests/test_auth.py::test_register_user -v
```

### Database
```bash
# Initialize/migrate database (called on app startup)
python -c "from app.database import init_db; init_db()"

# SQLite inspection (local development)
sqlite3 app.db ".tables"
sqlite3 app.db "SELECT * FROM user;"

# Reset database
rm app.db  # SQLite will recreate on next startup
```

### Environment Setup
```bash
# Copy template and configure
cp .env.example .env

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## High-Level Architecture

### Layered Architecture (Bottom to Top)

1. **Database Layer** (SQLite local / PostgreSQL production)
   - Models in `app/models.py`: User, Item, PasswordReset
   - Connection via SQLAlchemy ORM

2. **Data Layer** (`app/database.py`)
   - Engine and session management
   - Auto-migration for schema changes
   - Handles SQLite/PostgreSQL format differences

3. **Business Logic Layer**
   - `app/auth.py`: User authentication, session management (bcrypt + itsdangerous)
   - `app/services/scraper.py`: URL metadata extraction (YouTube API + web scraping)
   - `app/services/email.py`: Email delivery (SendGrid API + dev mode printing)
   - `app/config.py`: Centralized config from environment variables

4. **API Layer** (`app/main.py`)
   - FastAPI routes (REST endpoints)
   - Pydantic schemas for request/response validation
   - CORS and middleware configuration

5. **Presentation Layer** (`app/templates/`)
   - Jinja2 HTML templates
   - Alpine.js for client-side interactivity
   - Tailwind CSS for styling

### Key Data Models

```
User ─── (1:N) ─── Item
 │
 └──── (1:N) ─── PasswordReset
```

- **User**: email, hashed_password, created_at
- **Item**: url, title, description, source_type (youtube/article/other), completed, created_at
- **PasswordReset**: token, expires_at (1 hour), user_id

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/register` | Create new user + auto-login |
| POST | `/api/login` | Authenticate user |
| POST | `/api/logout` | Clear session |
| POST | `/api/items/add` | Add link with auto-scraped metadata |
| GET | `/api/items` | Fetch user's items (supports `status` filter) |
| PATCH | `/api/items/{id}` | Mark item completed/incomplete |
| DELETE | `/api/items/{id}` | Delete item |
| POST | `/api/forgot-password` | Initiate password reset (email sent) |
| POST | `/api/reset-password` | Complete password reset with token |

## Key Conventions

### Environment Variables & Configuration

- **Settings class** (`app/config.py`) is the single source of truth for all configuration
- All env vars loaded at app startup; missing `SECRET_KEY` raises `RuntimeError`
- Mock mode toggle: `USE_MOCK_EXTERNAL=true` (development) bypasses external APIs
- Database URL automatically normalizes Heroku PostgreSQL format (`postgres://` → `postgresql://`)

### Authentication & Security

- **Password hashing**: passlib + bcrypt (one-way hash, never store plaintext)
- **Session tokens**: itsdangerous `URLSafeTimedSerializer` (signed + timestamped)
- **Cookie storage**: HTTP-only + Secure flags (prevents XSS)
- **Session TTL**: 7 days (`SESSION_MAX_AGE` in config)
- **Dependency injection**: `get_current_user` and `get_current_user_id` as FastAPI dependencies

### Metadata Extraction (Scraping)

- **YouTube videos**: 
  - Try YouTube Data API v3 first (needs `YOUTUBE_API_KEY`)
  - Fallback to oEmbed API (no key, limited metadata)
  - Returns mock data in development (`[Mock]` prefix on title/description)
- **Regular web pages**: BeautifulSoup4 scrapes og:title/og:description meta tags
- **Graceful degradation**: Service continues even if external APIs fail (uses None values)

### Database Schema Handling

- **No migrations tool**: Tables auto-created by SQLAlchemy on first run
- **Schema evolution**: `init_db()` function in `app/database.py` checks for missing columns
- **SQLite specifics**: Uses `PRAGMA table_info()` for column detection
- **PostgreSQL specifics**: Queries `information_schema.columns` for column detection
- **Dual-database support**: Connection string detects SQLite (`:memory:` or `.db` files) vs PostgreSQL

### Naming & Code Style

- **Module organization**: Separate concerns into `auth.py`, `models.py`, `services/`, `templates/`
- **Type hints**: All function parameters and return types annotated (Python 3.8+)
- **Docstrings**: Use triple-quote docstrings for modules and functions
- **Comments**: Chinese and English mixed; comments explain "why", not "what"
- **Database defaults**: Timestamps use `datetime.datetime.utcnow` for UTC consistency

### Error Handling

- **HTTP exceptions**: Raise `HTTPException(status_code=..., detail=...)` for API errors
- **Session errors**: Invalid/expired sessions return 401 Unauthorized (not 403)
- **External API failures**: Log error, return None/mock data, don't crash
- **Validation**: Pydantic schemas validate all API inputs; invalid requests auto-reject with 422

### Testing Pattern (if adding tests)

- Use `pytest` + `pytest-asyncio` (already in requirements.txt)
- Create `tests/` directory with files like `test_auth.py`, `test_models.py`
- Use SQLite `:memory:` database for fast test isolation
- Dependency injection: override `get_db()` in tests to use test database

## External Integrations

### YouTube Data API v3
- **Config key**: `YOUTUBE_API_KEY` (optional in development)
- **Quota**: 10,000 units/day free tier; ~1 unit per video lookup
- **Console**: https://console.cloud.google.com/
- **Fallback**: oEmbed API (free, title only, no description)

### SendGrid Email Service
- **Config key**: `SENDGRID_API_KEY` (optional in development)
- **Dev behavior**: `USE_MOCK_EXTERNAL=true` prints reset link to console instead
- **Free tier**: 100 emails/day
- **Setup**: `SENDGRID_API_KEY=SG.xxxxx` and `FROM_EMAIL=noreply@example.com`

### Heroku Deployment
- **Procfile**: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Runtime**: Python 3.9 (specified in `runtime.txt`)
- **Database**: Auto-provisioned as `DATABASE_URL` env var (Heroku PostgreSQL add-on)
- **Buildpacks**: Python (auto-detected)

## Development Workflow

### Local Development
1. `.env` uses `USE_MOCK_EXTERNAL=true` and `DATABASE_URL=sqlite:///./app.db`
2. YouTube API returns `[Mock] ...` data when key not configured
3. Password reset emails print reset link to console
4. Full feature testing possible without external API keys

### Before Deployment
- Verify all routes work (run through TESTING.md checklist)
- Test with real API keys in staging if possible
- Check ARCHITECTURE.md for any pending migration notes

### Commit Conventions
- Reference issue numbers: `Fix #123: Add user email verification`
- Use present tense: "Add feature" not "Added feature"
- Keep commits focused (one feature/fix per commit)

## Common Tasks

### Adding a New Route
1. Add Pydantic schema in `app/schemas.py` (request/response)
2. Implement business logic in appropriate service or `auth.py`
3. Add route in `app/main.py` with `@app.post()` or `@app.get()` decorator
4. Use dependency injection: `db: Session = Depends(get_db)`, `user_id: int = Depends(get_current_user_id)`
5. Return appropriate Pydantic model for response

### Adding Database Fields
1. Update model in `app/models.py`
2. Add optional parameter to schema in `app/schemas.py`
3. Migration auto-runs on next startup (check `init_db()` in `database.py`)
4. If needed, update template to display new field

### Modifying Scraper Behavior
- Edit `app/services/scraper.py`
- Test with both real URLs and mock mode (`USE_MOCK_EXTERNAL=true`)
- YouTube logic: Try API → oEmbed → HTML parsing
- Web parsing: Handles og: meta tags, fallback to regular meta tags

### Debugging
- Enable `DEBUG=true` via environment (FastAPI auto-enables uvicorn debug mode)
- Check `app.config.py` to verify all env vars loaded correctly
- Print config with `settings.print_config()`
- Use `print()` statements; logs visible in console during development
