CREATE TABLE sections (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lab_id UUID REFERENCES labs(id) ON DELETE SET NULL,
    letter VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sections_course ON sections(course_id);
CREATE INDEX idx_sections_lab ON sections(lab_id);
CREATE INDEX idx_sections_letter ON sections(letter);

