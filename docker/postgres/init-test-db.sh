#!/usr/bin/env sh
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
CREATE DATABASE "$POSTGRES_TEST_DB";
SQL
