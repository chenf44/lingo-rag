"""Embed a pairs TSV and load it into Postgres (local Docker or Neon).

Usage:
    STORE=postgres python -m ingest.load --file data/sample/pairs.tsv
"""

import argparse
from pathlib import Path

from retrieval.embedding import build_embedder
from retrieval.search import Retriever, read_pairs
from retrieval.store import PostgresStore
from shared.config import get_settings


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=Path, default=Path("data/sample/pairs.tsv"))
    p.add_argument("--batch", type=int, default=200)
    args = p.parse_args()

    settings = get_settings()
    store = PostgresStore(settings.database_url, settings.embedding_dim)
    store.init_schema()
    retriever = Retriever(build_embedder(settings), store)

    sentences = read_pairs(args.file)
    for i in range(0, len(sentences), args.batch):
        retriever.index(sentences[i : i + args.batch])
        print(f"Indexed {min(i + args.batch, len(sentences))}/{len(sentences)}")
    print(f"Done. Table now holds {store.count()} sentences.")


if __name__ == "__main__":
    main()
