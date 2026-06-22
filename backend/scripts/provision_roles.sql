-- One-time database provisioning for multi-tenant RLS.
--
-- The application and tests MUST connect as a role WITHOUT the BYPASSRLS
-- attribute, or Row-Level Security is silently not enforced. Cloud Postgres
-- (e.g. Neon) often grants its default owner role BYPASSRLS. We therefore use
-- a dedicated `app_user` role for runtime/tests and reserve the owner role for
-- migrations (DDL).
--
-- Run as the database owner. Replace CHANGE_ME with a strong password.

-- 1) Create the application role (cluster-wide; run once).
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'CHANGE_ME' NOBYPASSRLS;
  END IF;
END $$;

-- 2) Per-database grants (run in EACH database: the app DB and the test DB).
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;
