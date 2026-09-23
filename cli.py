"""
CLI entrypoint for batch processing legal documents through the Task A pipeline.
"""

import argparse
import asyncio
import os
import sys
from typing import List

from src.db.database import AsyncSessionLocal
from src.pipeline.orchestrator import process_document_end_to_end


async def run_batch_ingestion(dir_path: str, source: str) -> None:
    """
    Ingest and process all PDF documents in a directory, displaying a summary table.
    """
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        print(f"Error: Directory path '{dir_path}' does not exist or is not a directory.")
        sys.exit(1)

    pdf_files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"No PDF documents found in directory '{dir_path}'.")
        return

    print(f"Starting Task A Legal Pipeline on {len(pdf_files)} PDF document(s)...")
    print(f"Source metadata: {source}\n")

    results = []

    async with AsyncSessionLocal() as session:
        for idx, file_path in enumerate(pdf_files, 1):
            filename = os.path.basename(file_path)
            print(f"[{idx}/{len(pdf_files)}] Processing {filename}...")
            res = await process_document_end_to_end(
                file_path=file_path,
                source=source,
                session=session,
            )
            results.append(res)
            print(f" -> Status: {res.status.upper()} (Stage: {res.stage})")

    # Print Summary Table
    success_count = sum(1 for r in results if r.status == "success")
    failed_count = sum(1 for r in results if r.status == "failed")
    duplicate_count = sum(1 for r in results if r.status == "duplicate")

    print("\n" + "=" * 60)
    print("                BATCH INGESTION SUMMARY RESULT               ")
    print("=" * 60)
    print(f" Total Processed : {len(pdf_files)}")
    print(f" Success         : {success_count}")
    print(f" Failed          : {failed_count}")
    print(f" Duplicate       : {duplicate_count}")
    print("=" * 60)

    if failed_count > 0:
        print("\nFailed Document Details:")
        for r in results:
            if r.status == "failed":
                print(f" - {os.path.basename(r.file_path)} [{r.stage}]: {r.error_message}")
    print("\nBatch processing completed.")


def main() -> None:
    """CLI argument parser main function."""
    parser = argparse.ArgumentParser(
        description="Task A Legal Dataset Ingestion & Pipeline CLI"
    )
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Path to directory containing PDF legal documents",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="Indian Courts Dataset",
        help="Source tag/label for provenance (default: 'Indian Courts Dataset')",
    )

    args = parser.parse_args()
    asyncio.run(run_batch_ingestion(dir_path=args.dir, source=args.source))


if __name__ == "__main__":
    main()
