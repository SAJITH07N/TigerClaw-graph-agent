"""
Batch Ingestion Script for IEEE-CIS 590,000 Transaction Fraud Dataset into TigerGraph.
Streams through train_transaction.csv and train_identity.csv in chunks and maps them into graph vertices & edges.
"""

import os
import sys
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IEEE-CIS-Ingester")


def ingest_dataset(
    tx_path: str,
    id_path: Optional[str] = None,
    limit: Optional[int] = None,
    chunk_size: int = 10000,
):
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for batch CSV ingestion. Install with `pip install pandas`.")
        sys.exit(1)

    from tigergraph.client import TigerGraphClient
    from data.ieee_cis_preprocessor import IEEECISPreprocessor

    tg_client = TigerGraphClient()
    preprocessor = IEEECISPreprocessor(tg_client)

    logger.info("Starting ingestion of IEEE-CIS dataset...")
    logger.info("Transactions CSV: %s", tx_path)
    logger.info("Identities CSV: %s", id_path or "None")

    identity_map = {}
    if id_path and os.path.exists(id_path):
        logger.info("Loading identity mapping records...")
        id_df = pd.read_csv(id_path)
        for _, row in id_df.iterrows():
            tx_id = str(row.get("TransactionID"))
            identity_map[tx_id] = row.to_dict()
        logger.info("Loaded %d identity records.", len(identity_map))

    total_ingested = 0
    for chunk_idx, chunk in enumerate(pd.read_csv(tx_path, chunksize=chunk_size)):
        for _, row in chunk.iterrows():
            rec = row.to_dict()
            tx_id = str(rec.get("TransactionID"))
            if tx_id in identity_map:
                rec.update(identity_map[tx_id])

            preprocessor.process_transaction_record(rec)
            total_ingested += 1

            if limit and total_ingested >= limit:
                break

        logger.info("Chunk %d processed. Cumulative transactions ingested: %d", chunk_idx + 1, total_ingested)
        if limit and total_ingested >= limit:
            break

    logger.info("Batch ingestion finished successfully! Total transactions loaded into graph: %d", total_ingested)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest IEEE-CIS dataset into TigerGraph Fraud Graph.")
    parser.add_argument("--train-tx", type=str, default="data/raw/train_transaction.csv", help="Path to train_transaction.csv")
    parser.add_argument("--train-id", type=str, default="data/raw/train_identity.csv", help="Path to train_identity.csv")
    parser.add_argument("--limit", type=int, default=None, help="Maximum transactions to ingest (default: all)")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Chunk size for streaming reads")

    args = parser.parse_args()
    if not os.path.exists(args.train_tx):
        logger.warning("Transactions file '%s' not found. For testing with sample data, use benchmark_runner.py.", args.train_tx)
    else:
        ingest_dataset(args.train_tx, args.train_id, args.limit, args.chunk_size)
