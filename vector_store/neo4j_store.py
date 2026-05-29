"""
Neo4j Graph Backend — Phase 5.

Optional graph database adapter that stores the intelligence knowledge graph
in Neo4j for advanced graph queries, pathfinding, and visualization.

Fully optional — when Neo4j is unavailable, the system gracefully degrades
to JSON-based storage.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

NEO4J_AVAILABLE = False
try:
    from neo4j import GraphDatabase, basic_auth
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    logger.debug("neo4j driver not installed — graph features disabled")


class Neo4jStore:
    """Manages the Neo4j knowledge graph for intelligence data."""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.driver = None
        self.enabled = False
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available; install with: pip install neo4j")
            return

        uri = uri or "bolt://localhost:7687"
        user = user or "neo4j"
        password = password or ""

        if not password:
            logger.warning("Neo4j password not configured — graph features disabled")
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
            self.driver.verify_connectivity()
            self.enabled = True
            logger.info("Connected to Neo4j at %s", uri)
        except ServiceUnavailable:
            logger.warning("Neo4j unavailable at %s — graph features disabled", uri)
        except AuthError:
            logger.warning("Neo4j auth failed at %s", uri)
        except Exception as e:
            logger.warning("Neo4j connection error: %s", e)

    def close(self):
        if self.driver:
            self.driver.close()

    def _run(self, query: str, params: Dict = None) -> Optional[List]:
        if not self.enabled or not self.driver:
            return None
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return list(result)
        except Exception as e:
            logger.debug("Neo4j query failed: %s", e)
            return None

    def clear_graph(self):
        self._run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j graph cleared")

    def store_entity(self, entity: str, entity_type: str, sector: str, confidence: float):
        self._run(
            """
            MERGE (e:Entity {name: $name})
            SET e.type = $type, e.sector = $sector,
                e.confidence = $confidence, e.updated_at = $updated
            """,
            {"name": entity, "type": entity_type, "sector": sector,
             "confidence": confidence, "updated": datetime.now().isoformat()},
        )

    def store_relationship(self, source: str, target: str,
                           weight: float, confidence: float,
                           sectors: List[str] = None,
                           causal: str = None):
        sectors = sectors or ["unknown"]
        props = {
            "weight": weight,
            "confidence": confidence,
            "source_sector": sectors[0],
            "target_sector": sectors[1] if len(sectors) > 1 else sectors[0],
            "causal_direction": causal or "bidirectional",
            "updated_at": datetime.now().isoformat(),
        }
        self._run(
            """
            MATCH (a:Entity {name: $source})
            MATCH (b:Entity {name: $target})
            MERGE (a)-[r:RELATES_TO]->(b)
            SET r += $props
            """,
            {"source": source, "target": target, "props": props},
        )

    def store_sector_edge(self, source_sector: str, target_sector: str,
                          link_count: int, avg_confidence: float):
        self._run(
            """
            MERGE (s:Sector {name: $src})
            MERGE (t:Sector {name: $tgt})
            MERGE (s)-[r:CROSS_DOMAIN]->(t)
            SET r.link_count = $count, r.avg_confidence = $conf,
                r.updated_at = $updated
            """,
            {"src": source_sector, "tgt": target_sector,
             "count": link_count, "conf": avg_confidence,
             "updated": datetime.now().isoformat()},
        )

    def store_sector_map(self, sector_map: Dict[str, Dict]):
        if not self.enabled:
            return
        for name, info in sector_map.items():
            self.store_entity(
                entity=name,
                entity_type=info.get("type", "unknown"),
                sector=info.get("sector", "unknown"),
                confidence=info.get("confidence", 0.5),
            )

    def store_cross_domain_links(self, links: List[Dict]):
        if not self.enabled:
            return
        for link in links:
            self.store_relationship(
                source=link["source_entity"],
                target=link["target_entity"],
                weight=link.get("strength", 0),
                confidence=link.get("confidence", 0),
                sectors=[link.get("source_sector", "unknown"),
                         link.get("target_sector", "unknown")],
                causal=link.get("causal_direction"),
            )

    def store_impact_chains(self, chains: List[Dict]):
        if not self.enabled:
            return
        for chain in chains:
            nodes = chain.get("chain", [])
            for i in range(len(nodes) - 1):
                self._run(
                    """
                    MATCH (a:Entity {name: $src})
                    MATCH (b:Entity {name: $tgt})
                    MERGE (a)-[r:IMPACT_CHAIN]->(b)
                    SET r.weight = $weight, r.hops = $hops
                    """,
                    {"src": nodes[i], "tgt": nodes[i+1],
                     "weight": chain.get("total_weight", 0),
                     "hops": chain.get("cross_domain_hops", 0)},
                )

    def get_entity(self, name: str) -> Optional[Dict]:
        result = self._run("MATCH (e:Entity {name: $name}) RETURN e", {"name": name})
        if result:
            return dict(result[0]["e"])
        return None

    def get_connections(self, entity: str, max_distance: int = 2) -> List[Dict]:
        result = self._run(
            """
            MATCH path = (e:Entity {name: $entity})-[*1..$max]-(connected)
            RETURN [n IN nodes(path) | n.name] AS path_nodes,
                   [r IN relationships(path) | r.confidence] AS confidences
            LIMIT 100
            """,
            {"entity": entity, "max": max_distance},
        )
        if not result:
            return []
        return [dict(r) for r in result]

    def get_sector_graph(self) -> Dict:
        result = self._run(
            "MATCH (s:Sector)-[r:CROSS_DOMAIN]->(t:Sector) "
            "RETURN s.name AS source, t.name AS target, r.link_count AS count"
        )
        nodes = set()
        edges = []
        if result:
            for r in result:
                nodes.add(r["source"])
                nodes.add(r["target"])
                edges.append({"source": r["source"], "target": r["target"],
                              "weight": r["count"]})
        return {"nodes": [{"id": n} for n in nodes], "edges": edges}

    def get_statistics(self) -> Dict:
        entities = self._run("MATCH (e:Entity) RETURN count(e) AS count")
        rels = self._run("MATCH ()-[r]->() RETURN count(r) AS count")
        sectors = self._run("MATCH (s:Sector) RETURN count(s) AS count")
        return {
            "entities": entities[0]["count"] if entities else 0,
            "relationships": rels[0]["count"] if rels else 0,
            "sectors": sectors[0]["count"] if sectors else 0,
            "enabled": self.enabled,
        }
