CREATE TABLE resource
(
    id            UUID PRIMARY KEY,
    resource_name VARCHAR(100) NOT NULL,
    description   VARCHAR(255),
    tags          VARCHAR(100)[],
    status        VARCHAR(10) DEFAULT 'FREE',
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resource_history
(
    id          UUID PRIMARY KEY,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource_id UUID REFERENCES resource(id) ON DELETE CASCADE, -- FK relationship
    operation   VARCHAR(10),
    description VARCHAR(255)
);

CREATE TABLE resource_variables
(
    id          UUID PRIMARY KEY,
    resource_id UUID REFERENCES resource(id) ON DELETE CASCADE, -- FK relationship
    name        VARCHAR(255),
    value       VARCHAR(255)
);