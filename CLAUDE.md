# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django Advanced Logging is a professional, scalable logging system for Python/Django projects with PostgreSQL support, async handlers, colored formatting, and sensitive data filtering. It's designed as a private/internal company package.

## Development Commands

### Setup
```bash
# Install dependencies
poetry install

# Install with dev dependencies
poetry install --with dev

# Install with docs dependencies
poetry install --with docs
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=django_advanced_logging

# Run specific test file
poetry run pytest tests/test_logger.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Run flake8 linter
poetry run flake8

# Type checking with mypy
poetry run mypy django_advanced_logging
```

### Django Integration Testing
The test suite uses `DJANGO_SETTINGS_MODULE = "tests.settings"` (configured in pyproject.toml). Ensure any Django-related tests have proper settings configuration.

## Architecture

### Core Components

**LoggerManager** (`core/logger.py`)
- Singleton pattern implementation for centralized logging management
- Manages logger instances, handlers, filters, and formatters
- Key methods: `get_logger()`, `log_exception()`, `log_function_call()` (decorator)
- Factory methods: `create_from_dict()`, `create_from_env()`
- **Important**: LogLevel and Environment constants are referenced but not defined in the file - they need to be added as enums/constants

**PostgreSQLHandler** (`core/handlers.py`)
- Asynchronous logging to PostgreSQL using thread-based queue
- Does NOT create tables automatically - tables must be created via Django migrations
- Uses batch writes (configurable batch_size and flush_interval)
- Thread-safe with automatic reconnection
- Stores custom fields as JSONB in `extra_data` column
- Statistics tracking via `get_statistics()`

**Formatters** (`core/formatters.py`)
- `ColoredFormatter`: ANSI color codes for console output (development)
- `JSONFormatter`: Structured JSON logs for production/aggregation systems
- **Bug**: JSONFormatter uses `json.dumps()` but doesn't import json module

**Filters** (`core/filters.py`)
- `EnvironmentFilter`: Adds environment info to log records
- `SensitiveDataFilter`: Masks sensitive data (passwords, tokens, API keys, etc.) using regex patterns

### Django Integration

**AppConfig** (`django/apps.py`)
- Auto-initializes logging when Django starts if `LOGGING_CONFIG` is in settings
- Prevents double initialization with `_initialized` flag
- Reads configuration from Django settings.LOGGING_CONFIG

**LoggingMiddleware** (`django/middleware.py`)
- Logs all HTTP requests/responses with timing
- Tracks: method, path, user, IP, user-agent, status code, duration
- Captures and logs exceptions with full context
- Also exports `ExternalIntegrationLoggingMiddleware` from integrations_middleware.py

**Migrations** (`django/migrations/0001_create_logs_table.py`)
- Creates `application_logs` table with proper schema
- Must be run before using PostgreSQLHandler: `python manage.py migrate`

### Utilities (`utils.py`)

Global logger manager pattern:
- `initialize_logging()`: Main initialization function (config object or kwargs)
- `initialize_from_env()`: Reads from environment variables (LOG_*, POSTGRES_*)
- `get_logger(name)`: Returns configured logger, auto-initializes if needed
- `log_execution()`: Decorator for automatic function execution logging
- `configure_django_logging()`: Django-specific configuration helper

## Configuration Pattern

The system uses two main configuration dataclasses:

**LogConfig** - Main logging configuration:
- Handles console/file output, rotation, formatting
- Environment-specific settings (development/staging/production)
- Integrates PostgreSQLConfig if postgres_enabled=True

**PostgreSQLConfig** - Database connection settings:
- Connection parameters (host, port, database, user, password)
- Async buffer settings (buffer_size, batch_size, flush_interval)
- Table configuration (table_name, schema)

## Important Notes

### Missing Implementations
1. **LogLevel and Environment constants** are referenced in `core/logger.py` but not defined
   - Should be enums or class constants (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Environment: DEVELOPMENT, STAGING, PRODUCTION

2. **Missing import in formatters.py**: `JSONFormatter` uses `json.dumps()` without importing json

3. **Test files are empty** - All test files in tests/ directory are placeholders (0 bytes)

### Database Requirements
- PostgreSQL is a **required** dependency (psycopg2-binary)
- Django is a **required** dependency (not optional)
- The logs table must exist before using PostgreSQLHandler - run migrations first
- PostgreSQLHandler no longer creates tables automatically (see _create_table() deprecation)

### Django Integration Workflow
1. Add `'django_advanced_logging'` to INSTALLED_APPS
2. Add `LOGGING_CONFIG` dict to settings.py
3. Run `python manage.py migrate` to create logs table
4. Optionally add middleware to MIDDLEWARE list
5. Use `get_logger(__name__)` in your code

### Singleton Behavior
LoggerManager implements singleton per `(name, environment)` combination. Multiple calls with same config return the same instance.

### Extra Fields Pattern
Custom data is passed via `extra={'extra_fields': {...}}` and stored as JSONB in PostgreSQL:
```python
logger.info("User action", extra={
    'extra_fields': {
        'user_id': 123,
        'action': 'login'
    }
})
```

### Thread Safety
- PostgreSQLHandler uses queue.Queue for thread-safe async writes
- Writer thread runs as daemon with graceful shutdown in close()
- Buffer overflow handling: drops oldest log when queue is full

## Package Distribution

This is a **private/proprietary** package (not open source):
- License: "Proprietary"
- Distribution: Git repository only (`pip install git+https://...`)
- Internal company use only
