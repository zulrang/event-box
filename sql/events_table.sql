CREATE TABLE events (
    id uuid         DEFAULT gen_random_uuid() PRIMARY KEY,
    topic           varchar(255) NOT NULL,
    partition_key   varchar(255) NOT NULL,
    class_name      varchar(255) NOT NULL,
    data jsonb      NOT NULL,
    created_at      timestamp NOT NULL DEFAULT NOW(),
    updated_at      timestamp NOT NULL DEFAULT NOW(),
    deleted_at      timestamp
);
