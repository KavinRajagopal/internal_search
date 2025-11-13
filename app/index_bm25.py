#!/usr/bin/env python3
"""
Index JSONL documents into OpenSearch with BM25 + vector search support.
"""

import json
from pathlib import Path
from opensearchpy import OpenSearch, helpers


def load_mapping(mapping_path):
    """Load OpenSearch mapping from JSON file."""
    with open(mapping_path, 'r') as f:
        return json.load(f)


def create_opensearch_client(host='localhost', port=9200):
    """Create OpenSearch client."""
    return OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False
    )


def create_index(client, index_name, mapping):
    """Create OpenSearch index with the given mapping if it doesn't exist."""
    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting it...")
        client.indices.delete(index=index_name)
    
    print(f"Creating index '{index_name}'...")
    client.indices.create(index=index_name, body=mapping)
    print(f"Index '{index_name}' created successfully.")


def read_jsonl(jsonl_path):
    """Read JSONL file and yield documents."""
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def bulk_index(client, index_name, jsonl_path, batch_size=100):
    """
    Bulk index documents from JSONL file into OpenSearch.
    
    Args:
        client: OpenSearch client
        index_name: Name of the index
        jsonl_path: Path to JSONL file
        batch_size: Number of documents to process per batch
    """
    print(f"Reading documents from: {jsonl_path}")
    
    def doc_generator():
        """Generator that yields documents for bulk indexing."""
        doc_count = 0
        for doc in read_jsonl(jsonl_path):
            doc_count += 1
            yield {
                "_index": index_name,
                "_id": doc.get("id"),
                "_source": doc
            }
            if doc_count % batch_size == 0:
                print(f"Prepared {doc_count} documents for indexing...")
    
    print("Starting bulk indexing...")
    success_count = 0
    error_count = 0
    
    try:
        # Use helpers.bulk for efficient bulk indexing
        for ok, response in helpers.streaming_bulk(
            client,
            doc_generator(),
            index=index_name,
            chunk_size=batch_size,
            max_retries=3,
            initial_backoff=2,
            max_backoff=600
        ):
            if ok:
                success_count += 1
                if success_count % 100 == 0:
                    print(f"Indexed {success_count} documents...")
            else:
                error_count += 1
                print(f"Error indexing document: {response}")
    
    except Exception as e:
        print(f"Error during bulk indexing: {e}")
        raise
    
    print(f"\nBulk indexing complete!")
    print(f"Successfully indexed: {success_count} documents")
    if error_count > 0:
        print(f"Errors: {error_count} documents")
    
    return success_count, error_count


def verify_index(client, index_name):
    """Verify index creation and get document count."""
    if not client.indices.exists(index=index_name):
        print(f"Error: Index '{index_name}' does not exist!")
        return False
    
    stats = client.indices.stats(index=index_name)
    doc_count = stats['indices'][index_name]['total']['docs']['count']
    
    print(f"\nIndex verification:")
    print(f"  Index name: {index_name}")
    print(f"  Document count: {doc_count}")
    
    return True


def index_jsonl_to_opensearch(
    jsonl_path,
    mapping_path,
    index_name='articles',
    host='localhost',
    port=9200
):
    """
    Main function to index JSONL documents into OpenSearch.
    
    Args:
        jsonl_path: Path to JSONL file
        mapping_path: Path to OpenSearch mapping JSON file
        index_name: Name of the OpenSearch index
        host: OpenSearch host
        port: OpenSearch port
    """
    # Load mapping
    print(f"Loading mapping from: {mapping_path}")
    mapping = load_mapping(mapping_path)
    
    # Create client
    print(f"Connecting to OpenSearch at {host}:{port}...")
    client = create_opensearch_client(host, port)
    
    # Test connection
    try:
        info = client.info()
        print(f"Connected to OpenSearch cluster: {info['cluster_name']}")
    except Exception as e:
        print(f"Error connecting to OpenSearch: {e}")
        raise
    
    # Create index
    create_index(client, index_name, mapping)
    
    # Bulk index documents
    success_count, error_count = bulk_index(client, index_name, jsonl_path)
    
    # Verify index
    verify_index(client, index_name)
    
    # Refresh index to make documents searchable immediately
    print("Refreshing index...")
    client.indices.refresh(index=index_name)
    print("Index refreshed. Documents are now searchable.")


if __name__ == "__main__":
    # Set paths
    base_dir = Path(__file__).parent.parent
    jsonl_path = base_dir / "data" / "articles.jsonl"
    mapping_path = base_dir / "opensearch" / "mapping.json"
    
    index_jsonl_to_opensearch(
        jsonl_path=jsonl_path,
        mapping_path=mapping_path,
        index_name='articles'
    )

