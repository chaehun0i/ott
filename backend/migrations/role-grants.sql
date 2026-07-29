-- Apply through a privileged migration connection after application schemas exist.
-- NOLOGIN roles keep credentials outside version control.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ott_api_runtime') THEN
    CREATE ROLE ott_api_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ott_worker_runtime') THEN
    CREATE ROLE ott_worker_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ott_backup_reader') THEN
    CREATE ROLE ott_backup_reader NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u02_migration_owner') THEN
    CREATE ROLE u02_migration_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u02_api_runtime') THEN
    CREATE ROLE u02_api_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u02_worker_runtime') THEN
    CREATE ROLE u02_worker_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u03_migration_owner') THEN
    CREATE ROLE u03_migration_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u03_api_runtime') THEN
    CREATE ROLE u03_api_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u03_worker_runtime') THEN
    CREATE ROLE u03_worker_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u04_migration_owner') THEN
    CREATE ROLE u04_migration_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u04_api_runtime') THEN
    CREATE ROLE u04_api_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u04_worker_runtime') THEN
    CREATE ROLE u04_worker_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u05_migration_owner') THEN
    CREATE ROLE u05_migration_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u05_api_runtime') THEN
    CREATE ROLE u05_api_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'u05_maintenance_runtime') THEN
    CREATE ROLE u05_maintenance_runtime NOLOGIN;
  END IF;
END
$$;

GRANT SELECT, INSERT, UPDATE ON idempotency_records, outbox_jobs TO ott_api_runtime;
GRANT SELECT, INSERT, UPDATE ON outbox_jobs TO ott_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ott_backup_reader;

GRANT USAGE ON SCHEMA u02_identity TO u02_api_runtime, u02_worker_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA u02_identity TO u02_api_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA u02_identity TO u02_worker_runtime;
GRANT SELECT, INSERT, UPDATE ON outbox_jobs TO u02_api_runtime, u02_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u02_identity TO ott_backup_reader;

GRANT USAGE ON SCHEMA u03_catalog TO u03_api_runtime, u03_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u03_catalog TO u03_api_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA u03_catalog TO u03_worker_runtime;
GRANT SELECT, INSERT, UPDATE ON outbox_jobs TO u03_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u03_catalog TO ott_backup_reader;

GRANT USAGE ON SCHEMA u04_ingestion TO u04_api_runtime, u04_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u04_ingestion TO u04_api_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA u04_ingestion TO u04_worker_runtime;
GRANT SELECT, INSERT, UPDATE ON outbox_jobs TO u04_worker_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u04_ingestion TO ott_backup_reader;

GRANT USAGE ON SCHEMA u05_recommendation TO u05_api_runtime, u05_maintenance_runtime;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA u05_recommendation TO u05_api_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA u05_recommendation TO u05_maintenance_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA u05_recommendation TO ott_backup_reader;
