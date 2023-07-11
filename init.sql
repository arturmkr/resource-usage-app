CREATE TABLE resource (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    tags JSON,
    status VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

INSERT INTO resource (id, name, description, tags, status, created_at)
VALUES
    ('3620f982-d189-4acf-b806-3cab4e50b1b9', 'server1', 'primary', '["azure"]', 'FREE', now()),
    ('177ea420-8ba0-4057-9d6d-984e1ebd2355', 'server2', 'backup', '["azure", "aws"]', 'BLOCKED', now());