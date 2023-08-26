-- postgres
CREATE TABLE resource
(
    id            UUID PRIMARY KEY,
    resource_name VARCHAR(100) NOT NULL,
    description   VARCHAR(255),
    tags          VARCHAR(100)[],
    status        VARCHAR(10) DEFAULT 'FREE',
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO resource (id, resource_name, description, tags, status, created_at)
VALUES ('3620f982-d189-4acf-b806-3cab4e50b1b9',
        'server1',
        'primary',
        ARRAY ['azure'],
        'FREE',
        current_timestamp),
       ('177ea420-8ba0-4057-9d6d-984e1ebd2355',
        'server2',
        'backup',
        ARRAY ['azure', 'aws'],
        'BLOCKED',
        current_timestamp);

CREATE TABLE resource_history
(
    id          UUID PRIMARY KEY,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource_id UUID,
    operation   VARCHAR(10),
    description VARCHAR(255)
);