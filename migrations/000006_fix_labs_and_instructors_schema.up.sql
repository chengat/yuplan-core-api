-- Alter labs table: remove course_id, add section_id
ALTER TABLE labs DROP CONSTRAINT IF EXISTS labs_course_id_fkey;
DROP INDEX IF EXISTS idx_labs_course;
ALTER TABLE labs DROP COLUMN IF EXISTS course_id;
ALTER TABLE labs ADD COLUMN section_id UUID REFERENCES sections(id) ON DELETE CASCADE;
CREATE INDEX idx_labs_section ON labs(section_id);

-- Alter instructors table: add section_id
ALTER TABLE instructors ADD COLUMN section_id UUID REFERENCES sections(id) ON DELETE SET NULL;
CREATE INDEX idx_instructors_section ON instructors(section_id);

