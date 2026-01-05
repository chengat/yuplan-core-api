-- Create section_activities table to consolidate labs, tutorials, and other activity types
CREATE TABLE section_activities (
    id UUID PRIMARY KEY,
    course_type VARCHAR(10) NOT NULL,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    catalog_number VARCHAR(200) NOT NULL,
    times TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_section_activities_section ON section_activities(section_id);
CREATE INDEX idx_section_activities_catalog ON section_activities(catalog_number);
CREATE INDEX idx_section_activities_type ON section_activities(course_type);

-- Migrate data from labs table
INSERT INTO section_activities (id, course_type, section_id, catalog_number, times, created_at, updated_at)
SELECT id, 'LAB', section_id, catalog_number, times, created_at, updated_at
FROM labs;

-- Migrate data from tutorials table
INSERT INTO section_activities (id, course_type, section_id, catalog_number, times, created_at, updated_at)
SELECT id, 'TUTR', section_id, catalog_number, times, created_at, updated_at
FROM tutorials;

-- Drop old tables
DROP TABLE IF EXISTS labs CASCADE;
DROP TABLE IF EXISTS tutorials CASCADE;

-- Remove times column from sections (all times now in section_activities)
ALTER TABLE sections DROP COLUMN IF EXISTS times;
