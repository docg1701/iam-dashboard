-- PostgreSQL initialization script for IAM Dashboard
-- This script runs when the database is first created

-- Create development database (if not exists)
SELECT 'CREATE DATABASE iam_dashboard_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'iam_dashboard_dev');

-- Create test database (if not exists)
SELECT 'CREATE DATABASE iam_dashboard_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'iam_dashboard_test');

-- Create application user (if not exists in production)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'iam_dashboard_user') THEN

      CREATE ROLE iam_dashboard_user LOGIN PASSWORD 'iam_dashboard_password';
   END IF;
END
$do$;

-- Grant permissions on main database
GRANT CONNECT ON DATABASE iam_dashboard TO iam_dashboard_user;
GRANT USAGE ON SCHEMA public TO iam_dashboard_user;
GRANT CREATE ON SCHEMA public TO iam_dashboard_user;

-- Grant permissions on development database
GRANT CONNECT ON DATABASE iam_dashboard_dev TO iam_dashboard_user;

-- Grant permissions on test database
GRANT CONNECT ON DATABASE iam_dashboard_test TO iam_dashboard_user;

-- Create extensions (if needed)
\c iam_dashboard;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c iam_dashboard_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c iam_dashboard_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Log initialization completion
\echo 'PostgreSQL initialization completed for IAM Dashboard'