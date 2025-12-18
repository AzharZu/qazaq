-- PostgreSQL initialization script for Qazaq platform
-- This script runs automatically when the postgres container first starts

-- Create database (optional, as it's already specified in compose environment)
-- CREATE DATABASE qazaq_db;

-- Create user with password (optional, already specified in compose environment)
-- CREATE USER qazaq_user WITH PASSWORD 'qazaq_pass';

-- Grant all privileges on database to user
GRANT ALL PRIVILEGES ON DATABASE qazaq_db TO qazaq_user;

-- Connect to the database
\c qazaq_db

-- Grant schema privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO qazaq_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qazaq_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO qazaq_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO qazaq_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO qazaq_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO qazaq_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO qazaq_user;
