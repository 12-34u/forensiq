"""Graph schema definitions for the Neo4j forensic knowledge graph."""

from __future__ import annotations

# ────────────────────────────────────────────────────────
# Node labels
# ────────────────────────────────────────────────────────

class NodeLabel:
    PROJECT = "Project"              # top-level grouping node per ingest
    PERSON = "Person"
    PHONE_NUMBER = "PhoneNumber"
    EMAIL_ADDRESS = "EmailAddress"
    DEVICE = "Device"
    APP = "App"
    ACCOUNT = "Account"
    LOCATION = "Location"
    URL = "URL"
    PAGE = "Page"                  # links to the PageIndex page
    ORGANIZATION = "Organization"
    FILE = "File"


# ────────────────────────────────────────────────────────
# Relationship types
# ────────────────────────────────────────────────────────

class RelType:
    # Person / Contact edges
    HAS_PHONE = "HAS_PHONE"
    HAS_EMAIL = "HAS_EMAIL"
    BELONGS_TO_ORG = "BELONGS_TO_ORG"
    HAS_ACCOUNT = "HAS_ACCOUNT"

    # Communication edges
    CALLED = "CALLED"
    MESSAGED = "MESSAGED"
    EMAILED = "EMAILED"

    # Device edges
    OWNS_DEVICE = "OWNS_DEVICE"
    INSTALLED_ON = "INSTALLED_ON"

    # Location edges
    VISITED = "VISITED"
    LOCATED_AT = "LOCATED_AT"

    # Web
    BROWSED = "BROWSED"

    # Page provenance
    MENTIONED_IN = "MENTIONED_IN"
    EXTRACTED_FROM = "EXTRACTED_FROM"

    # Project grouping
    PART_OF = "PART_OF"


# ────────────────────────────────────────────────────────
# Cypher statements for schema initialisation
# ────────────────────────────────────────────────────────

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person)       REQUIRE p.uid IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:PhoneNumber)  REQUIRE n.number IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:EmailAddress) REQUIRE e.address IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device)       REQUIRE d.uid IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:App)          REQUIRE a.package IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ac:Account)     REQUIRE ac.uid IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location)     REQUIRE l.uid IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:URL)          REQUIRE u.address IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (pg:Page)        REQUIRE pg.page_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Project)     REQUIRE pr.project_id IS UNIQUE",
]
