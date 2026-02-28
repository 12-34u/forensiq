"""Neo4j client – manages the driver, schema, and CRUD operations."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import GraphDatabase, Session

from config.settings import settings
from forensiq.graphrag.schema import SCHEMA_CONSTRAINTS

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Wrapper around the Neo4j Python driver."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> None:
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._database = database or settings.neo4j_database
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
        logger.info("Neo4j driver initialised → %s (db=%s)", self._uri, self._database)

    # ── lifecycle ─────────────────────────────────────

    def close(self) -> None:
        self._driver.close()

    def verify(self) -> bool:
        """Check connectivity."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.error("Neo4j connectivity check failed: %s", exc)
            return False

    # ── schema ────────────────────────────────────────

    def ensure_schema(self) -> None:
        """Create uniqueness constraints if they don't exist yet."""
        with self._driver.session(database=self._database) as session:
            for stmt in SCHEMA_CONSTRAINTS:
                try:
                    session.run(stmt)
                except Exception as exc:
                    logger.debug("Constraint may already exist: %s", exc)
        logger.info("Neo4j schema constraints ensured")

    # ── generic write ─────────────────────────────────

    def run_write(self, cypher: str, **params: Any) -> list[dict]:
        with self._driver.session(database=self._database) as session:
            result = session.run(cypher, **params)
            return [dict(r) for r in result]

    def run_read(self, cypher: str, **params: Any) -> list[dict]:
        with self._driver.session(database=self._database) as session:
            result = session.run(cypher, **params)
            return [dict(r) for r in result]

    # ── node helpers ──────────────────────────────────

    def merge_node(self, label: str, key_field: str, key_value: str, props: dict | None = None):
        """MERGE a node by its unique key and set additional properties."""
        prop_str = ""
        params: dict[str, Any] = {"key_val": key_value}
        if props:
            set_parts = []
            for i, (k, v) in enumerate(props.items()):
                pname = f"p{i}"
                set_parts.append(f"n.{k} = ${pname}")
                params[pname] = v
            prop_str = "SET " + ", ".join(set_parts)

        cypher = f"MERGE (n:{label} {{{key_field}: $key_val}}) {prop_str} RETURN n"
        self.run_write(cypher, **params)

    def merge_relationship(
        self,
        src_label: str,
        src_key: str,
        src_val: str,
        rel_type: str,
        dst_label: str,
        dst_key: str,
        dst_val: str,
        props: dict | None = None,
    ):
        """MERGE a relationship between two nodes identified by their unique keys."""
        prop_str = ""
        params: dict[str, Any] = {"src_val": src_val, "dst_val": dst_val}
        if props:
            set_parts = []
            for i, (k, v) in enumerate(props.items()):
                pname = f"rp{i}"
                set_parts.append(f"r.{k} = ${pname}")
                params[pname] = v
            prop_str = "SET " + ", ".join(set_parts)

        cypher = (
            f"MERGE (a:{src_label} {{{src_key}: $src_val}}) "
            f"MERGE (b:{dst_label} {{{dst_key}: $dst_val}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) {prop_str} "
            "RETURN type(r)"
        )
        self.run_write(cypher, **params)

    # ── batch helpers (for cloud / high-latency) ─────

    def batch_merge_nodes(self, label: str, key_field: str, items: list[dict]) -> None:
        """Batch-MERGE a list of nodes using UNWIND.

        Each item in *items* must have a ``key_value`` and optionally ``props``.
        """
        if not items:
            return
        cypher = (
            f"UNWIND $items AS item "
            f"MERGE (n:{label} {{{key_field}: item.key_value}}) "
            f"SET n += item.props"
        )
        with self._driver.session(database=self._database) as session:
            session.run(cypher, items=items)

    def batch_merge_relationships(self, items: list[dict]) -> None:
        """Batch-MERGE relationships using UNWIND.

        Each item dict must have: src_label, src_key, src_val, rel_type,
        dst_label, dst_key, dst_val, and optionally rel_props.
        Items are grouped by (src_label, dst_label, rel_type) for efficiency.
        """
        if not items:
            return
        from collections import defaultdict
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for it in items:
            key = (it["src_label"], it["src_key"], it["rel_type"], it["dst_label"], it["dst_key"])
            groups[key].append(it)

        with self._driver.session(database=self._database) as session:
            for (src_label, src_key, rel_type, dst_label, dst_key), group in groups.items():
                batch = [
                    {"src_val": g["src_val"], "dst_val": g["dst_val"], "rel_props": g.get("rel_props", {})}
                    for g in group
                ]
                cypher = (
                    f"UNWIND $batch AS item "
                    f"MERGE (a:{src_label} {{{src_key}: item.src_val}}) "
                    f"MERGE (b:{dst_label} {{{dst_key}: item.dst_val}}) "
                    f"MERGE (a)-[r:{rel_type}]->(b) "
                    f"SET r += item.rel_props"
                )
                session.run(cypher, batch=batch)

    # ── query helpers ─────────────────────────────────

    def get_neighbours(self, label: str, key_field: str, key_value: str, depth: int = 1) -> list[dict]:
        """Return all nodes within *depth* hops of a given node."""
        cypher = (
            f"MATCH (n:{label} {{{key_field}: $key_val}})-[r*1..{depth}]-(m) "
            "RETURN DISTINCT labels(m) AS labels, properties(m) AS props"
        )
        return self.run_read(cypher, key_val=key_value)

    def count_nodes(self) -> int:
        rows = self.run_read("MATCH (n) RETURN count(n) AS cnt")
        return rows[0]["cnt"] if rows else 0

    def count_relationships(self) -> int:
        rows = self.run_read("MATCH ()-[r]->() RETURN count(r) AS cnt")
        return rows[0]["cnt"] if rows else 0
