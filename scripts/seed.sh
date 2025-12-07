#!/bin/bash

# Seed script for populating the DB

set -e

echo "Seeding database..."

DATABASE_URL="${DATABASE_URL:-postgres://yuplan_core_api_user:yuplan_core_api_password@postgres:5432/yuplan_core_api_db?sslmode=disable}"

until pg_isready -h postgres -U yuplan_core_api_user -d yuplan_core_api_db; do
  echo "Waiting for postgres to be ready..."
  sleep 2
done

echo "Postgres is ready. Seeding database..."

# Run seed file
if [ -f "./db/seed.sql" ]; then
    PGPASSWORD=yuplan_core_api_password psql -h postgres -U yuplan_core_api_user -d yuplan_core_api_db -f ./db/seed.sql
    echo "Database seeded successfully!"
else
    echo "Error: seed.sql file not found. Skipping seeding."
fi

