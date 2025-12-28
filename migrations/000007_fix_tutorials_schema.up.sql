-- Alter tutorials table: remove course_id, add section_id
ALTER TABLE tutorials DROP CONSTRAINT IF EXISTS tutorials_course_id_fkey;
DROP INDEX IF EXISTS idx_tutorials_course;
ALTER TABLE tutorials DROP COLUMN IF EXISTS course_id;
ALTER TABLE tutorials ADD COLUMN section_id UUID REFERENCES sections(id) ON DELETE CASCADE;
CREATE INDEX idx_tutorials_section ON tutorials(section_id);
