#!/bin/bash

# Runs DB migrations

set -e

echo "Running database migrations..."

DATABASE_URL="${DATABASE_URL:-postgres://yuplan_core_api_user:yuplan_core_api_password@postgres:5432/yuplan_core_api_db?sslmode=disable}"

until pg_isready -h postgres -U yuplan_core_api_user -d yuplan_core_api_db; do
  echo "Waiting for postgres to be ready..."
  sleep 2
done

echo "Postgres is ready. Running migrations..."

migrate -path ./migrations -database "$DATABASE_URL" up

echo "Migrations completed successfully!"

