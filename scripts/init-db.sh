#!/bin/bash

# Runs migrations and seeds database

set -e

echo "Initializing database..."

# 1. Run migrations
./scripts/migrate.sh

# 2. Seed the database
./scripts/seed.sh

echo "Database initialization complete!"

