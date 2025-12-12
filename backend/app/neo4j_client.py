from __future__ import annotations

from typing import Any, Dict, List

from neo4j import GraphDatabase, Driver

from .config import get_settings


driver: Driver | None = None


def get_driver() -> Driver:
    global driver
    if driver is None:
        settings = get_settings()
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return driver


def write_entities(entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> None:
    def _write(tx):
        for entity in entities:
            tx.run(
                "MERGE (n:Entity {name: $name}) SET n += $props",
                name=entity["name"],
                props=entity.get("properties", {}),
            )
        for rel in relationships:
            if not rel.get("start") or not rel.get("end"):
                continue
            tx.run(
                """
                MATCH (a:Entity {name: $start}), (b:Entity {name: $end})
                MERGE (a)-[r:RELATED {type: $type}]->(b)
                SET r += $props
                """,
                start=rel["start"],
                end=rel["end"],
                type=rel.get("type", "related_to"),
                props=rel.get("properties", {}),
            )

    driver = get_driver()
    with driver.session(database=get_settings().neo4j_database) as session:
        session.execute_write(_write)


def query_graph(entity_names: List[str]) -> List[Dict[str, Any]]:
    if not entity_names:
        return []

    cypher = """
    MATCH (e:Entity)-[r]->(target)
    WHERE e.name IN $names OR target.name IN $names
    RETURN e.name AS source, type(r) AS rel_type, target.name AS target, r as rel_props, e as source_props, target as target_props
    LIMIT 50
    """
    driver = get_driver()
    with driver.session(database=get_settings().neo4j_database) as session:
        result = session.run(cypher, names=entity_names)
        data = []
        for record in result:
            data.append(
                {
                    "source": record["source"],
                    "relationship": record["rel_type"],
                    "target": record["target"],
                    "source_properties": dict(record["source_props"]),
                    "target_properties": dict(record["target_props"]),
                    "relationship_properties": dict(record["rel_props"]),
                }
            )
        return data
