CREATE TABLE courses (
    id UUID PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    code VARCHAR(50) NOT NULL,
    credits DECIMAL(4, 2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_courses_code ON courses(code);

