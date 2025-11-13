#!/usr/bin/env python3
"""
Convert Fake.csv to JSONL format with embeddings for OpenSearch indexing.
"""

import json
import pandas as pd
from sentence_transformers import SentenceTransformer
from dateutil import parser
from pathlib import Path


def parse_date(date_str):
    """Convert date string like 'December 31, 2017' to ISO format '2017-12-31'."""
    try:
        dt = parser.parse(date_str)
        return dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return None


def convert_csv_to_jsonl(csv_path, jsonl_path, embedding_model_name='sentence-transformers/all-MiniLM-L6-v2'):
    """
    Convert CSV to JSONL format with embeddings.
    
    Args:
        csv_path: Path to input CSV file
        jsonl_path: Path to output JSONL file
        embedding_model_name: Name of the sentence transformer model
    """
    print(f"Loading embedding model: {embedding_model_name}")
    model = SentenceTransformer(embedding_model_name)
    
    print(f"Reading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Processing {len(df)} rows...")
    
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for idx, row in df.iterrows():
            # Generate sequential ID (1-indexed)
            doc_id = idx + 1
            
            # Parse date
            date_iso = parse_date(row['date']) if pd.notna(row['date']) else None
            
            # Combine title and text for embedding
            title = str(row['title']) if pd.notna(row['title']) else ""
            text = str(row['text']) if pd.notna(row['text']) else ""
            embedding_text = f"{title} {text}".strip()
            
            # Generate embedding
            embedding = model.encode(embedding_text, show_progress_bar=False).tolist()
            
            # Map subject to tags array
            tags = [row['subject']] if pd.notna(row['subject']) else []
            
            # Create document matching OpenSearch mapping
            doc = {
                "id": str(doc_id),
                "title": title if title else None,
                "excerpt": text if text else None,  # Full text in excerpt
                "body_text": text if text else None,
                "url": None,
                "image": None,
                "tags": tags,
                "author": None,
                "site_id": None,
                "status": None,
                "published_at": date_iso,
                "updated_at": date_iso,
                "acl_groups": None,
                "embedding": embedding
            }
            
            # Write as JSON line
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{len(df)} rows...")
    
    print(f"Conversion complete! Output written to: {jsonl_path}")


if __name__ == "__main__":
    # Set paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "data" / "Fake.csv"
    jsonl_path = base_dir / "data" / "articles.jsonl"
    
    convert_csv_to_jsonl(csv_path, jsonl_path)


