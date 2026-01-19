# core-api service

API for course data. Serves courses, instructors, and sections to core-web.

## Data Pipeline

Course data flows through: Source (HTML) → JSON → SQL → Seeds Database

Scrapers in `scraping/scrapers/` extract course data from HTML and write JSON files to `scraping/data/`. The `scripts/generate_seed.py` script converts JSON files into SQL (`db/seed.sql`), which is loaded into the database on startup.

## Setup

Run with Docker Compose:

```bash
docker-compose up --build
```

The API runs on port 8080. Database migrations and seeding run automatically.

## Rough Design (First Iteration)

<img width="582" height="504" alt="image" src="https://github.com/user-attachments/assets/cecbfcd0-87a2-495b-b30e-c76baa2e37bd" />

## Endpoints

- `GET /api/v1/courses` - List all courses
- `GET /api/v1/courses/search` - Search courses
- `GET /api/v1/courses/:course_code` - Get a course by course code (returns all term offerings, hydrated with sections/activities)
- `GET /api/v1/instructors/:course_id` - Get instructors for a course
- `GET /api/v1/sections/:course_id` - Get sections + section_activities for a course

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (default: `postgres://postgres:postgres@localhost:5432/yuplan?sslmode=disable`)
- `PORT` - Server port (default: `8080`)
