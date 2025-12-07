CREATE TABLE labs (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    catalog_number VARCHAR(200) NOT NULL,
    times TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_labs_course ON labs(course_id);
CREATE INDEX idx_labs_catalog ON labs(catalog_number);

