#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<--EOSQL
-- Create a customer role and set permissions
  CREATE ROLE "customer" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "customer";
  GRANT USAGE ON SCHEMA public TO "customer";
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO "customer";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "r-user";
-- Create a teller role and set permissions
  CREATE ROLE "teller" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "teller";
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "teller";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "teller";
-- Create an admin role and set permissions
  CREATE ROLE "administrator" WITH NOLOGIN;
  GRANT CONNECT ON DATABASE bankTest TO "customer";
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "administrator";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "administrator";
-- Create users and assign roles
  CREATE USER "bailee" WITH PASSWORD 'asdf1234';
  GRANT "administrator" TO "bailee";
-- Create table
  CREATE TYPE user-type AS ENUM ('customer', 'teller', 'administrator');
  CREATE TABLE bankTest (user user-type NOT NULL, value DOUBLE
PRECISION, temperature DOUBLE PRECISION);
-- Convert the table to a hypertable with a 15 minute chunk interval
  SELECT create_hypertable('data', by_range('time', INTERVAL '15 mintues'));
EOSQL