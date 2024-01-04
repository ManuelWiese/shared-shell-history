#!/bin/bash

DATABASE=$1
TABLE_NAME="bash_commands"


# Connect to the PostgreSQL database and execute the SQL commands
psql -q -d $DATABASE -c "
    -- Create the table
    DO \$$
    BEGIN
        IF NOT EXISTS(
            SELECT 1
            FROM pg_tables
            WHERE tablename='$TABLE_NAME'
        ) THEN
            CREATE TABLE IF NOT EXISTS $TABLE_NAME (
                user_name VARCHAR NOT NULL,
                host VARCHAR NOT NULL,
                path VARCHAR NOT NULL,
                venv VARCHAR NOT NULL,
                command VARCHAR NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        END IF;
    END \$$;

    -- Create a function for the trigger
    CREATE OR REPLACE FUNCTION update_command_time()
    RETURNS TRIGGER AS \$$
    BEGIN
        NEW.time = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    \$$ LANGUAGE plpgsql;

    -- Create the trigger
    -- DROP TRIGGER IF EXISTS before_insert_user_commands ON $TABLE_NAME;
    DO \$$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger
            WHERE tgname='before_insert_user_commands'
        ) THEN
            CREATE TRIGGER before_insert_user_commands
            BEFORE INSERT ON $TABLE_NAME
            FOR EACH ROW EXECUTE FUNCTION update_command_time();
        END IF;
    END \$$;
"