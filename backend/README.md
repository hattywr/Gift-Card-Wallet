# Gift Card Wallet Backend API

This is the backend API for the Gift Card Wallet mobile app. It's built with FastAPI, SQLAlchemy, and MySQL.

## Features

- User authentication with JWT tokens
- Gift card management
- Vendor management
- Image storage for gift cards and vendor logos
- Comprehensive logging
- Rate limiting and security features

## Prerequisites

- Python 3.8+
- MySQL database
- Virtual environment (optional but recommended)

## Installation

1. Clone the repository
2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file based on the template in `config.py`
2. Configure your database connection and other settings

## Database Setup

1. Create a MySQL database:
   ```sql
   CREATE DATABASE gift_card_wallet;
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

## Running the API

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
pytest
```

For more details on testing, see the [tests README](tests/README.md).

### Creating a New Migration

When you've made changes to your models:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

```bash
alembic upgrade head
```

### API Structure

- `app/main.py`: Main application entry point
- `app/models.py`: Database models
- `app/schemas.py`: Pydantic models for validation
- `app/database.py`: Database configuration
- `app/auth.py`: Authentication logic
- `app/security.py`: Security utilities
- `app/routers/`: API route handlers
  - `users.py`: User profile management
  - `vendors.py`: Vendor management
  - `gift_cards.py`: Gift card management

## Directory Structure

```
backend/
   app/
      routers/
         __init__.py
         gift_cards.py
         users.py
         vendors.py
      utils/
         __init__.py
         security.py
      auth.py
      config.py
      database.py
      logger.py
      main.py
      models.py
      schemas.py
      security.py
   migrations/
      versions/
      env.py
      script.py.mako
   tests/
      unit/
      integration/
      conftest.py
      README.md
   logs/
   alembic.ini
   requirements.txt
   README.md
```