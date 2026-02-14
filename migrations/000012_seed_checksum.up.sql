-- Store seed.sql checksum so we only truncate+re-seed when seed file changes (reviews table is never touched)
CREATE TABLE IF NOT EXISTS _seed_checksum (checksum TEXT);
