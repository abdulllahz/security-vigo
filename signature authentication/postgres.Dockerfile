FROM postgres:latest
COPY migrations.sql /docker-entrypoint-initdb.d/