"""
1-Click TigerGraph Savanna / Community Edition Deployment Script.
Connects to TigerGraph via pyTigerGraph or RESTPP, creates the FraudGraph schema,
installs all 10 GSQL queries, seeds 100 historical closed cases, and verifies health.
"""

import os
import sys
import glob
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TG-Deployer")

try:
    import pyTigerGraph as tg
except ImportError:
    logger.warning("pyTigerGraph not installed. Install with `pip install pyTigerGraph` for remote deployment.")
    tg = None


def deploy_to_tigergraph():
    host = os.getenv("TG_HOST", "https://your-savanna-instance.i.tgcloud.io")
    graph_name = os.getenv("TG_GRAPH_NAME", "FraudGraph")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    secret = os.getenv("TG_SECRET", "")

    logger.info("Connecting to TigerGraph instance at: %s", host)

    if not tg:
        logger.error("pyTigerGraph is required to deploy schema and queries to a live TigerGraph cluster.")
        sys.exit(1)

    try:
        conn = tg.TigerGraphConnection(
            host=host,
            graphname=graph_name,
            username=username,
            password=password,
        )

        if secret:
            conn.getToken(secret)
            logger.info("Authenticated successfully with TigerGraph RESTPP token.")
        else:
            logger.info("Connected with username/password.")

        # 1. Deploy Schema DDL
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "schema.gsql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_gsql = f.read()
            logger.info("Deploying 14-Vertex, 10-Edge Schema DDL...")
            res = conn.gsql(schema_gsql)
            logger.info("Schema DDL result: %s", res)

        # 2. Deploy & Install all 10 GSQL queries
        gsql_dir = os.path.join(os.path.dirname(__file__), "..", "schema")
        query_files = glob.glob(os.path.join(gsql_dir, "*.gsql"))

        for q_file in query_files:
            if os.path.basename(q_file) == "schema.gsql":
                continue
            q_name = os.path.splitext(os.path.basename(q_file))[0]
            logger.info("Installing query: %s", q_name)
            with open(q_file, "r", encoding="utf-8") as f:
                q_content = f.read()
            # Create query
            conn.gsql(f"USE GRAPH {graph_name}\n{q_content}")

        logger.info("Compiling and installing all installed queries (INSTALL QUERY ALL)...")
        conn.gsql(f"USE GRAPH {graph_name}\nINSTALL QUERY ALL")
        logger.info("All 10 GSQL queries compiled and live on TigerGraph endpoint!")

        # 3. Seed Historical Memory
        from tigergraph.client import TigerGraphClient
        from data.seed_historical_memory import seed_historical_memory
        tg_client = TigerGraphClient(host=host, graph_name=graph_name, username=username, password=password, secret=secret)
        logger.info("Seeding 100 historical closed cases into TigerGraph...")
        count = seed_historical_memory(tg_client, count=100)
        logger.info("Successfully seeded %d historical memory cases into live graph!", count)

        # 4. Verify connectivity
        v_count = conn.getVertexCount("*")
        e_count = conn.getEdgeCount("*")
        logger.info("Live Graph Status -> Total Vertices: %s | Total Edges: %s", v_count, e_count)
        print("\nDeployment complete! Your TigerGraph Savanna cluster is ready for agent investigations.")

    except Exception as e:
        logger.error("Deployment failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    deploy_to_tigergraph()
