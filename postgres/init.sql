CREATE USER root;
CREATE DATABASE recipes;
GRANT ALL PRIVILEGES ON DATABASE recipes TO root;

\c recipes;
CREATE TABLE IF NOT EXISTS recipes (
    title TEXT,
    ingredients TEXT,
    method TEXT
);

CREATE TABLE updates (
    title TEXT,
    ingredients TEXT,
    method TEXT
);