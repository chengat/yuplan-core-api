-- Restore times column to sections (if it was removed)
ALTER TABLE sections ADD COLUMN IF NOT EXISTS times TEXT;

-- Recreate labs table
CREATE TABLE labs (
    id UUID PRIMARY KEY,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    catalog_number VARCHAR(200) NOT NULL,
    times TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_labs_section ON labs(section_id);
CREATE INDEX idx_labs_catalog ON labs(catalog_number);

-- Recreate tutorials table
CREATE TABLE tutorials (
    id UUID PRIMARY KEY,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    catalog_number VARCHAR(200) NOT NULL,
    times TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tutorials_section ON tutorials(section_id);
CREATE INDEX idx_tutorials_catalog ON tutorials(catalog_number);

-- Migrate data back from section_activities
INSERT INTO labs (id, section_id, catalog_number, times, created_at, updated_at)
SELECT id, section_id, catalog_number, times, created_at, updated_at
FROM section_activities
WHERE course_type = 'LAB';

INSERT INTO tutorials (id, section_id, catalog_number, times, created_at, updated_at)
SELECT id, section_id, catalog_number, times, created_at, updated_at
FROM section_activities
WHERE course_type = 'TUTR';

-- Drop section_activities table
DROP TABLE IF EXISTS section_activities CASCADE;
