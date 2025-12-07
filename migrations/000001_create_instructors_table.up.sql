CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE instructors (
    id UUID PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    rate_my_prof_link TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_instructors_name ON instructors(last_name, first_name);

