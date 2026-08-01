CREATE TYPE status AS ENUM ('FREE', 'BLOCKED');
CREATE TYPE resourceoperationtype AS ENUM ('BLOCK', 'RELEASE');

CREATE TABLE resource
(
    id            UUID PRIMARY KEY,
    resource_name VARCHAR(100) NOT NULL,
    description   VARCHAR(255),
    tags          VARCHAR[] NOT NULL DEFAULT '{}',
    status        status NOT NULL DEFAULT 'FREE',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_resource_free_tags ON resource USING GIN (tags) WHERE status = 'FREE';

CREATE TABLE resource_history
(
    id          UUID PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resource_id UUID NOT NULL REFERENCES resource (id) ON DELETE CASCADE,
    operation   resourceoperationtype NOT NULL,
    description VARCHAR(255)
);

CREATE INDEX ix_resource_history_resource_id ON resource_history (resource_id);

CREATE TABLE resource_variables
(
    id          UUID PRIMARY KEY,
    resource_id UUID NOT NULL REFERENCES resource (id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    value       VARCHAR(255) NOT NULL
);
