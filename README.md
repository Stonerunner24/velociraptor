# Velociraptor - Enterprise RAG Tree Processing System

A tree-based approach for processing documents in Enterprise RAG systems. Velociraptor takes large documents and recursively splits them into a hierarchical tree structure stored in a graph database, preserving document structure while enabling granular search and retrieval.

## Features

- **Hierarchical Document Processing**: Recursively splits large documents into manageable tree structures
- **AI-Powered Summaries**: Generates summaries at each level of the tree using Anthropic Claude
- **Semantic Search**: Uses embeddings for similarity-based content discovery
- **Graph Database Storage**: Stores document trees in Neo4j for efficient querying
- **Intelligent Navigation**: Navigate through document structure with parent/child/sibling relationships
- **Context Preservation**: Maintains document structure while enabling granular access

## Architecture

```
Document (PDF) → Tree Structure → AI Summaries → Embeddings → Graph Database → Search & Navigation
```

### Core Components

1. **DocumentSplitter**: Recursively splits documents into hierarchical chunks
2. **DocumentSummarizer**: Generates AI summaries for each node in the tree
3. **EmbeddingGenerator**: Creates embeddings for semantic search
4. **Neo4jConnector**: Manages graph database operations
5. **SemanticSearchEngine**: Handles similarity-based search
6. **TreeNavigator**: Provides document navigation capabilities

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up Neo4j Database**:
   - Install Neo4j Desktop or use Neo4j Aura
   - Create a new database
   - Note the connection details

3. **Configure Environment Variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

Required environment variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `NEO4J_URI`: Neo4j database URI (e.g., bolt://localhost:7687)
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

## Quick Start

```python
from src import Velociraptor

# Initialize the system
with Velociraptor() as raptor:
    # Process a document
    document_id = raptor.process_document("large_document.pdf", "My Document")
    
    # Search for content
    results = raptor.search("artificial intelligence", top_k=5)
    
    # Get document outline
    outline = raptor.get_document_outline(document_id)
    
    # Navigate through the document
    context = raptor.get_node_context(results[0]['node'].id)
    parent = raptor.navigate_to_parent(results[0]['node'].id)
```

## How It Works

### 1. Document Processing
- **Root Node**: The entire document becomes the root node
- **Recursive Splitting**: Documents are split recursively until reaching manageable leaf nodes
- **Configurable Chunking**: Set chunk size (pages per chunk) based on your needs

### 2. AI Enhancement
- **Leaf Summaries**: Claude generates summaries from full text at leaf nodes
- **Hierarchical Summaries**: Parent nodes contain summaries of their children's summaries
- **Embeddings**: Generated using sentence-transformers for semantic search

### 3. Graph Storage
- **Neo4j Integration**: Stores the entire tree structure in a graph database
- **Relationship Preservation**: Maintains parent-child relationships and document structure
- **Efficient Querying**: Optimized for tree traversal and similarity search

### 4. Search Experience
- **Semantic Search**: Users search via semantic similarity on embeddings
- **Contextual Navigation**: AI agents can navigate document structure
- **Granular Access**: Access specific sections while maintaining broader context

## API Reference

### Main Class

```python
raptor = Velociraptor(
    anthropic_api_key="your-key",
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j", 
    neo4j_password="password",
    max_chunk_size=10  # pages per chunk
)
```

### Key Methods

- `process_document(pdf_path, title)`: Process and store a document
- `search(query, document_id, top_k)`: Search for similar content
- `get_document_outline(document_id)`: Get hierarchical document structure
- `get_node_context(node_id)`: Get navigation context for a node
- `navigate_to_parent/children/siblings(node_id)`: Navigate through document
- `get_related_sections(node_id)`: Find related content sections

## Example Usage

See `example.py` for a complete example that demonstrates:
- Document processing
- Semantic search
- Document navigation
- Context retrieval
- Related section discovery

## Configuration

### Chunk Size Configuration
```python
# Small chunks (1-5 pages) - more granular
raptor = Velociraptor(max_chunk_size=5)

# Large chunks (10-20 pages) - broader context
raptor = Velociraptor(max_chunk_size=20)
```

### Search Parameters
```python
# Adjust search sensitivity
results = raptor.search(
    query="machine learning",
    document_id=doc_id,
    top_k=10,
    threshold=0.7  # similarity threshold
)
```

## Key Advantages

1. **Structure Preservation**: Unlike traditional chunking, maintains document hierarchy
2. **Contextual Understanding**: AI understands both specific content and broader context
3. **Flexible Navigation**: Move between sections, drill down, or zoom out as needed
4. **Semantic Discovery**: Find relevant content even with different terminology
5. **Scalable Storage**: Graph database efficiently handles large document collections

## Performance Considerations

- **Chunk Size**: Smaller chunks provide more granular search but require more processing
- **Embedding Cost**: Embeddings are generated for leaf nodes only to optimize costs
- **Database Indexing**: Proper Neo4j indexing is crucial for search performance
- **Parallel Processing**: Components can be parallelized for large document collections

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**: Ensure Neo4j is running and credentials are correct
2. **Anthropic API Error**: Check API key and rate limits
3. **PDF Processing Error**: Ensure PDF is readable and not password-protected
4. **Memory Issues**: Reduce chunk size or process documents in batches

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.