#!/bin/bash
set -e

databases=("cmdb_ipam" "cmdb_auth" "cmdb_tenant" "cmdb_event" "cmdb_webhook")

for db in "${databases[@]}"; do
    echo "Creating database: $db"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
        GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
EOSQL
done

echo "All databases created successfully."
