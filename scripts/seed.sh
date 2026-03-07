#!/bin/bash

# Seed script for populating the DB

set -e

echo "Seeding database..."

# Use DATABASE_URL from environment (provided by Render)
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Ensure SSL mode is set correctly (Supabase need SSL, docker-compose does not)
SEED_URL="$DATABASE_URL"
if [[ "$SEED_URL" != *"sslmode"* ]]; then
    if [[ "$SEED_URL" == *"supabase.co"* ]] || [[ "$SEED_URL" == *"@dpg-"* ]]; then
        if [[ "$SEED_URL" == *"?"* ]]; then
            SEED_URL="${SEED_URL}&sslmode=require"
        else
            SEED_URL="${SEED_URL}?sslmode=require"
        fi
    elif [[ "$SEED_URL" == *"@postgres:"* ]]; then
        if [[ "$SEED_URL" == *"?"* ]]; then
            SEED_URL="${SEED_URL}&sslmode=disable"
        else
            SEED_URL="${SEED_URL}?sslmode=disable"
        fi
    fi
fi

# Selective seeding: TRUNCATE then INSERT so we never duplicate. Only refresh tables seed.sql fills; reviews never touched.
if [ ! -f "./db/seed.sql" ]; then
    echo "Warning: seed.sql file not found. Skipping seeding."
    exit 0
fi

current_sha=$( (sha256sum ./db/seed.sql 2>/dev/null || shasum -a 256 ./db/seed.sql) | awk '{print $1}')
stored_sha=$(psql "$SEED_URL" -t -A -c "SELECT checksum FROM _seed_checksum LIMIT 1" 2>/dev/null || true)
stored_sha="${stored_sha%%[[:space:]]*}"

if [ -n "$stored_sha" ] && [ "$current_sha" = "$stored_sha" ]; then
    echo "seed.sql unchanged (checksum match). Skipping selective seed."
    exit 0
fi

echo "seed.sql changed or first run. Truncating only seed tables (reviews untouched), then seeding..."
psql "$SEED_URL" -c "TRUNCATE instructors, section_activities, sections, courses RESTART IDENTITY CASCADE;"
psql "$SEED_URL" -f ./db/seed.sql
psql "$SEED_URL" -c "DELETE FROM _seed_checksum; INSERT INTO _seed_checksum (checksum) VALUES ('$current_sha');"
echo "Database seeded successfully!"

