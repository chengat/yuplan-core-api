-- Junction table for instructors and courses (many-to-many)
CREATE TABLE instructor_courses (
    instructor_id UUID NOT NULL REFERENCES instructors(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    PRIMARY KEY (instructor_id, course_id)
);

CREATE INDEX idx_instructor_courses_instructor ON instructor_courses(instructor_id);
CREATE INDEX idx_instructor_courses_course ON instructor_courses(course_id);

