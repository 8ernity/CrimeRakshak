import os
from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

print(f"Testing connectivity to {uri} with user: {user}")
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("SUCCESS: Connected to Neo4j database")
    driver.close()
except Exception as e:
    print(f"FAILED: Could not connect to Neo4j ({e})")

