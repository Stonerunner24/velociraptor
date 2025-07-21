#!/usr/bin/env python3
"""
Velociraptor MCP Server

An MCP (Model Context Protocol) server that exposes Velociraptor document processing
capabilities to Claude Desktop and other MCP clients.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

from src import Velociraptor

# Initialize the MCP server
server = Server("velociraptor")

# Global Velociraptor instance
velociraptor_instance: Optional[Velociraptor] = None

def get_velociraptor() -> Velociraptor:
    """Get or create Velociraptor instance"""
    global velociraptor_instance
    if velociraptor_instance is None:
        velociraptor_instance = Velociraptor(max_chunk_size=50)
    return velociraptor_instance

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="process_document",
            description="Process a PDF document and store it in the Velociraptor system",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file to process"
                    },
                    "document_title": {
                        "type": "string", 
                        "description": "Optional title for the document"
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="search_documents",
            description="Search for content across processed documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Optional document ID to restrict search to"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_documents",
            description="List all processed documents",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_document_stats",
            description="Get statistics for a specific document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID"
                    }
                },
                "required": ["document_id"]
            }
        ),
        Tool(
            name="get_document_outline",
            description="Get the hierarchical outline of a document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID"
                    }
                },
                "required": ["document_id"]
            }
        ),
        Tool(
            name="get_node_context",
            description="Get context information for a specific node in the document tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node ID"
                    }
                },
                "required": ["node_id"]
            }
        ),
        Tool(
            name="get_related_sections",
            description="Get sections related to a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node ID"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of related sections to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["node_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    raptor = get_velociraptor()
    
    try:
        if name == "process_document":
            pdf_path = arguments["pdf_path"]
            document_title = arguments.get("document_title", "")
            
            document_id = raptor.process_document(pdf_path, document_title)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Document processed successfully. Document ID: {document_id}"
                )
            ]
        
        elif name == "search_documents":
            query = arguments["query"]
            document_id = arguments.get("document_id")
            top_k = arguments.get("top_k", 5)
            
            results = raptor.search(query, document_id=document_id, top_k=top_k)
            
            if not results:
                return [types.TextContent(type="text", text="No results found")]
            
            result_text = f"Found {len(results)} results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                result_text += f"{i}. Pages {result['page_range']} (similarity: {result['similarity']:.3f})\n"
                result_text += f"   Preview: {result['preview'][:200]}...\n\n"
            
            return [types.TextContent(type="text", text=result_text)]
        
        elif name == "list_documents":
            documents = raptor.list_documents()
            
            if not documents:
                return [types.TextContent(type="text", text="No documents found")]
            
            doc_list = f"Found {len(documents)} documents:\n\n"
            for doc in documents:
                doc_list += f"- {doc['title']} (ID: {doc['id']})\n"
            
            return [types.TextContent(type="text", text=doc_list)]
        
        elif name == "get_document_stats":
            document_id = arguments["document_id"]
            stats = raptor.get_document_stats(document_id)
            
            stats_text = f"Document Statistics for {document_id}:\n"
            for key, value in stats.items():
                stats_text += f"  {key}: {value}\n"
            
            return [types.TextContent(type="text", text=stats_text)]
        
        elif name == "get_document_outline":
            document_id = arguments["document_id"]
            outline = raptor.get_document_outline(document_id)
            
            if not outline:
                return [types.TextContent(type="text", text="No outline found for this document")]
            
            def format_outline(items, indent=0):
                result = ""
                for item in items:
                    prefix = "  " * indent
                    result += f"{prefix}- {item['page_range']}: {item['summary'][:100]}...\n"
                    if item.get('children'):
                        result += format_outline(item['children'], indent + 1)
                return result
            
            outline_text = f"Document Outline:\n{format_outline(outline)}"
            return [types.TextContent(type="text", text=outline_text)]
        
        elif name == "get_node_context":
            node_id = arguments["node_id"]
            context = raptor.get_node_context(node_id)
            
            context_text = f"Node Context:\n"
            context_text += f"Current: {context['current']['page_range']}\n"
            context_text += f"Summary: {context['current']['summary']}\n\n"
            
            if context.get('parent'):
                context_text += f"Parent: {context['parent']['page_range']}\n"
                context_text += f"Parent Summary: {context['parent']['summary'][:100]}...\n\n"
            
            if context.get('children'):
                context_text += f"Children ({len(context['children'])}):\n"
                for child in context['children']:
                    context_text += f"  - {child['page_range']}: {child['summary'][:50]}...\n"
            
            return [types.TextContent(type="text", text=context_text)]
        
        elif name == "get_related_sections":
            node_id = arguments["node_id"]
            top_k = arguments.get("top_k", 5)
            related = raptor.get_related_sections(node_id, top_k=top_k)
            
            if not related:
                return [types.TextContent(type="text", text="No related sections found")]
            
            related_text = f"Related Sections:\n"
            for rel in related:
                related_text += f"- {rel['page_range']} (similarity: {rel['similarity']:.3f})\n"
                related_text += f"  {rel['preview'][:100]}...\n\n"
            
            return [types.TextContent(type="text", text=related_text)]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server"""
    # Import here to avoid issues if mcp is not installed
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="velociraptor",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())