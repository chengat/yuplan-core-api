-- Revert tutorials table: remove section_id, add back course_id
DROP INDEX IF EXISTS idx_tutorials_section;
ALTER TABLE tutorials DROP COLUMN IF EXISTS section_id;
ALTER TABLE tutorials ADD COLUMN course_id UUID REFERENCES courses(id) ON DELETE CASCADE;
CREATE INDEX idx_tutorials_course ON tutorials(course_id);
