-- Immutable local synthetic calibration evidence by Jason Stys; identifiers: docs/CODE_INDEX.md.
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, report_json TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON runs BEGIN SELECT RAISE(ABORT,'Immutable evidence'); END;
CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON runs BEGIN SELECT RAISE(ABORT,'Immutable evidence'); END;
