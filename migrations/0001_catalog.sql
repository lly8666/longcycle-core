CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS evidence;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE core.taxonomies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL,
    version text NOT NULL,
    name text NOT NULL,
    description text,
    valid_from date,
    valid_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (code, version),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.taxonomy_nodes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    taxonomy_id uuid NOT NULL REFERENCES core.taxonomies(id),
    code text NOT NULL,
    slug text NOT NULL,
    canonical_name text NOT NULL,
    node_kind text NOT NULL,
    archetype text,
    active boolean NOT NULL DEFAULT true,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (taxonomy_id, code),
    UNIQUE (taxonomy_id, slug),
    UNIQUE (taxonomy_id, id),
    CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')
);

CREATE TABLE core.taxonomy_edges (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    taxonomy_id uuid NOT NULL REFERENCES core.taxonomies(id),
    parent_node_id uuid NOT NULL,
    child_node_id uuid NOT NULL,
    relation_type text NOT NULL DEFAULT 'parent_child',
    valid_from date,
    valid_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (taxonomy_id, parent_node_id, child_node_id, relation_type, valid_from),
    FOREIGN KEY (taxonomy_id, parent_node_id) REFERENCES core.taxonomy_nodes(taxonomy_id, id),
    FOREIGN KEY (taxonomy_id, child_node_id) REFERENCES core.taxonomy_nodes(taxonomy_id, id),
    CHECK (parent_node_id <> child_node_id),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type text NOT NULL,
    canonical_name text NOT NULL,
    normalized_name text NOT NULL,
    country_code char(2),
    lifecycle_status text NOT NULL DEFAULT 'active',
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (entity_type IN (
        'organization_group', 'legal_entity', 'issuer', 'security', 'facility',
        'production_line', 'mine', 'port', 'product', 'project', 'event'
    ))
);

CREATE TABLE core.entity_names (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_id uuid NOT NULL REFERENCES core.entities(id),
    name text NOT NULL,
    normalized_name text NOT NULL,
    name_type text NOT NULL,
    language_code text,
    valid_from date,
    valid_to date,
    source_assertion_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (entity_id, normalized_name, name_type, valid_from),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.entity_identifiers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_id uuid NOT NULL REFERENCES core.entities(id),
    namespace text NOT NULL,
    identifier_value text NOT NULL,
    normalized_value text NOT NULL,
    valid_from date,
    valid_to date,
    source_assertion_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (namespace, normalized_value, valid_from),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.entity_relation_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id uuid NOT NULL REFERENCES core.entities(id),
    to_entity_id uuid NOT NULL REFERENCES core.entities(id),
    relation_type text NOT NULL,
    ownership_ratio numeric(12, 9),
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    resolution_id uuid,
    confidence double precision NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (from_entity_id <> to_entity_id),
    CHECK (ownership_ratio IS NULL OR ownership_ratio BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE core.industry_entity_memberships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    entity_id uuid NOT NULL REFERENCES core.entities(id),
    role text NOT NULL,
    exposure_type text,
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    confidence double precision NOT NULL,
    resolution_id uuid,
    UNIQUE (industry_node_id, entity_id, role, valid_from, system_from),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE core.products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id uuid NOT NULL UNIQUE REFERENCES core.entities(id),
    product_family_id uuid REFERENCES core.products(id),
    canonical_name text NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE core.product_specs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL REFERENCES core.products(id),
    spec_code text NOT NULL,
    specification jsonb NOT NULL,
    comparability_hash text NOT NULL,
    valid_from date,
    valid_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (product_id, spec_code, valid_from),
    UNIQUE NULLS NOT DISTINCT (product_id, comparability_hash, valid_from),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.facilities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id uuid NOT NULL UNIQUE REFERENCES core.entities(id),
    facility_type text NOT NULL,
    country_code char(2),
    region text,
    latitude numeric(9, 6),
    longitude numeric(9, 6),
    commissioned_on date,
    permanently_closed_on date,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CHECK (permanently_closed_on IS NULL OR commissioned_on IS NULL OR permanently_closed_on >= commissioned_on)
);

CREATE TABLE core.production_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id uuid NOT NULL UNIQUE REFERENCES core.entities(id),
    facility_id uuid NOT NULL REFERENCES core.facilities(id),
    line_code text,
    technology text,
    commissioned_on date,
    permanently_closed_on date,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (facility_id, line_code),
    CHECK (permanently_closed_on IS NULL OR commissioned_on IS NULL OR permanently_closed_on >= commissioned_on)
);

CREATE TABLE core.security_listings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    security_entity_id uuid NOT NULL REFERENCES core.entities(id),
    issuer_entity_id uuid NOT NULL REFERENCES core.entities(id),
    exchange_code text NOT NULL,
    ticker text NOT NULL,
    security_type text NOT NULL,
    currency_code char(3),
    listed_on date,
    delisted_on date,
    valid_from date,
    valid_to date,
    UNIQUE NULLS NOT DISTINCT (exchange_code, ticker, valid_from),
    CHECK (delisted_on IS NULL OR listed_on IS NULL OR delisted_on >= listed_on),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE core.units (
    code text PRIMARY KEY,
    dimension text NOT NULL,
    display_name text NOT NULL,
    decimal_scale smallint NOT NULL DEFAULT 6,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE core.predicate_definitions (
    code text NOT NULL,
    schema_version text NOT NULL,
    canonical_name text NOT NULL,
    value_kinds text[] NOT NULL,
    temporal_mode text NOT NULL,
    dimension_schema_version text NOT NULL,
    required_dimensions text[] NOT NULL DEFAULT '{}',
    allowed_dimensions text[] NOT NULL DEFAULT '{}',
    canonical_unit_code text REFERENCES core.units(code),
    high_impact boolean NOT NULL DEFAULT false,
    reconciliation_policy jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (code, schema_version),
    CHECK (cardinality(value_kinds) > 0),
    CHECK (temporal_mode IN ('period', 'timeless')),
    CHECK (required_dimensions <@ allowed_dimensions)
);

CREATE TABLE core.unit_conversion_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    from_unit text NOT NULL REFERENCES core.units(code),
    to_unit text NOT NULL REFERENCES core.units(code),
    multiplier numeric(40, 18) NOT NULL,
    additive_offset numeric(40, 18) NOT NULL DEFAULT 0,
    valid_from date,
    valid_to date,
    source_assertion_id uuid,
    UNIQUE NULLS NOT DISTINCT (from_unit, to_unit, valid_from),
    CHECK (from_unit <> to_unit),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE INDEX taxonomy_edges_parent_idx ON core.taxonomy_edges (parent_node_id, valid_from);
CREATE INDEX taxonomy_edges_child_idx ON core.taxonomy_edges (child_node_id, valid_from);
CREATE INDEX entities_name_trgm_idx ON core.entities USING gin (normalized_name gin_trgm_ops);
CREATE INDEX entity_names_trgm_idx ON core.entity_names USING gin (normalized_name gin_trgm_ops);
CREATE INDEX entity_identifiers_lookup_idx ON core.entity_identifiers (namespace, normalized_value);
CREATE INDEX entity_relations_from_idx ON core.entity_relation_versions (from_entity_id, relation_type, valid_from);
CREATE INDEX entity_relations_to_idx ON core.entity_relation_versions (to_entity_id, relation_type, valid_from);
CREATE INDEX industry_memberships_industry_idx ON core.industry_entity_memberships (industry_node_id, role, valid_from);
CREATE INDEX industry_memberships_entity_idx ON core.industry_entity_memberships (entity_id, role, valid_from);
CREATE UNIQUE INDEX predicate_definitions_one_active_idx
    ON core.predicate_definitions (code) WHERE active;
