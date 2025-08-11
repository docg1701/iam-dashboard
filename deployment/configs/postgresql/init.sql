-- PostgreSQL initialization script for IAM Dashboard
-- This script runs when the database is first created

-- Create development and test databases
-- Note: CREATE DATABASE cannot be executed inside a transaction block or function
-- So we'll handle this through multiple connections in the script

-- First, ensure extensions are created on main database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

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

-- Log initialization completion
\echo 'PostgreSQL initialization completed for IAM Dashboard'