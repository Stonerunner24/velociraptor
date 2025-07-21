# Velociraptor MCP Server

This document explains how to set up Velociraptor as an MCP (Model Context Protocol) server for use with Claude Desktop.

## Setup Instructions

### 1. Install MCP Dependencies

```bash
pip install mcp
```

### 2. Configure Claude Desktop

Add the following configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "velociraptor": {
      "command": "python3",
      "args": ["/path/to/your/velociraptor/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here",
        "NEO4J_URI": "neo4j://127.0.0.1:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-neo4j-password"
      }
    }
  }
}
```

**Important**: Replace the file path and environment variables with your actual values.

### 3. Start Neo4j Database

Make sure your Neo4j database is running before using the MCP server:

```bash
# If using Docker
docker run --name neo4j -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/raptor01 neo4j:latest

# Or start your local Neo4j instance
```

### 4. Test the Server

You can test the MCP server directly:

```bash
python3 mcp_server.py
```

## Available Tools

The Velociraptor MCP server provides the following tools:

### Document Processing
- **process_document**: Process a PDF document and store it in the system
- **list_documents**: List all processed documents
- **get_document_stats**: Get statistics for a specific document

### Search & Navigation
- **search_documents**: Search for content across processed documents
- **get_document_outline**: Get the hierarchical outline of a document
- **get_node_context**: Get context information for a specific node
- **get_related_sections**: Get sections related to a specific node

## Usage Examples

Once configured in Claude Desktop, you can use these tools by asking Claude to:

1. **Process a document**: "Process the PDF at /path/to/document.pdf"
2. **Search documents**: "Search for information about banking regulations"
3. **Get document outline**: "Show me the outline of the banking document"
4. **Find related sections**: "Find sections related to this node ID"

## Troubleshooting

1. **Server won't start**: Check that all dependencies are installed and environment variables are set
2. **Neo4j connection fails**: Ensure Neo4j is running and credentials are correct
3. **Permission errors**: Make sure the Python script is executable and paths are correct

## Security Notes

- Keep your API keys secure and don't commit them to version control
- Consider using environment variables or a secure key management system
- Ensure your Neo4j instance is properly secured if exposed to the network