-- Revert labs table changes
DROP INDEX IF EXISTS idx_labs_section;
ALTER TABLE labs DROP COLUMN IF EXISTS section_id;
ALTER TABLE labs ADD COLUMN course_id UUID REFERENCES courses(id) ON DELETE CASCADE;
CREATE INDEX idx_labs_course ON labs(course_id);

-- Revert instructors table changes
DROP INDEX IF EXISTS idx_instructors_section;
ALTER TABLE instructors DROP COLUMN IF EXISTS section_id;

