#!/bin/bash

# Startup script for Render deployment and docker-compose
# Runs migrations, seeds database, then starts the server
# Automatically detects docker-compose vs Render

set -e

echo "Starting application..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "DATABASE_URL is configured"

# In docker-compose, migrate service runs migrations+seed; here we only start the app
if [[ "$DATABASE_URL" == *"@postgres:"* ]]; then
    echo "Detected docker-compose - skipping migrations and seeding (handled by migrate service)"
else
    # Supabase (DB): run migrations then selective seed (no duplicates, seed.sh uses checksum + TRUNCATE)
    echo "Running migrations and selective seed..."
    
    # Give the database a moment to be ready (Render databases can take a few seconds)
    echo "Waiting a moment for database to be ready..."
    sleep 3

    # Run migrations (migrate tool will handle connection retries)
    echo "Running database migrations..."
    ./scripts/migrate.sh

    # Seed the database (psql will handle connection retries)
    echo "Seeding database..."
    ./scripts/seed.sh
fi

# Start the server (Go app will handle connection retries)
echo "Starting API server..."
exec /app/bin/api
