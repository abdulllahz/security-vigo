CREATE DATABASE authentication;
\c authentication;
CREATE USER bykea_auth WITH PASSWORD 'bykea_123';
GRANT ALL PRIVILEGES ON DATABASE authentication TO bykea_auth;
CREATE TABLE records (
  fingerprint TEXT,
  key TEXT
);