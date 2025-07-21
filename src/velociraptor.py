"""
Velociraptor - Tree-based Document Processing for Enterprise RAG

Main orchestrator class that combines all components
"""

from typing import Dict, Any, List, Optional
import os
from pathlib import Path

from .models import DocumentTree, DocumentNode
from .processors import DocumentSplitter  
from .ai import DocumentSummarizer, EmbeddingGenerator
from .database import Neo4jConnector
from .search import SemanticSearchEngine
from .navigation import TreeNavigator

class Velociraptor:
    """Main class for the Velociraptor document processing system"""
    
    def __init__(self, 
                 anthropic_api_key: Optional[str] = None,
                 neo4j_uri: Optional[str] = None,
                 neo4j_username: Optional[str] = None, 
                 neo4j_password: Optional[str] = None,
                 max_chunk_size: int = 10):
        """
        Initialize Velociraptor with configuration
        
        Args:
            anthropic_api_key: Anthropic API key for AI operations
            neo4j_uri: Neo4j database URI
            neo4j_username: Neo4j username
            neo4j_password: Neo4j password
            max_chunk_size: Maximum pages per chunk
        """
        # Initialize components
        self.splitter = DocumentSplitter(max_chunk_size=max_chunk_size)
        self.summarizer = DocumentSummarizer(api_key=anthropic_api_key)
        self.embedding_generator = EmbeddingGenerator()
        self.db_connector = Neo4jConnector(neo4j_uri, neo4j_username, neo4j_password)
        self.search_engine = SemanticSearchEngine(self.embedding_generator, self.db_connector)
        self.navigator = TreeNavigator(self.db_connector)
        
        # Initialize database
        self.db_connector.create_indexes()
    
    def process_document(self, pdf_path: str, document_title: str = "") -> str:
        """
        Process a PDF document and store it in the system
        
        Args:
            pdf_path: Path to the PDF file
            document_title: Optional title for the document
            
        Returns:
            Document ID of the processed document
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(pdf_path)
        
        # Extract title from filename if not provided
        if not document_title:
            document_title = Path(pdf_path).stem
        
        print(f"Processing document: {document_title}")
        
        # Step 1: Split document into tree structure
        print("1. Splitting document into tree structure...")
        tree = self.splitter.process_document(pdf_path, document_title)
        
        # Step 2: Generate summaries for all nodes
        print("2. Generating summaries...")
        self.summarizer.generate_summaries_for_tree(tree)
        
        # Step 3: Generate embeddings for leaf nodes
        print("3. Generating embeddings...")
        self.embedding_generator.generate_embeddings_for_tree(tree)
        
        # Step 4: Store in graph database
        print("4. Storing in database...")
        self.db_connector.store_document_tree(tree)
        
        print(f"Document processed successfully. Document ID: {tree.document_id}")
        return tree.document_id
    
    def search(self, query: str, 
               document_id: Optional[str] = None,
               top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for content similar to the query
        
        Args:
            query: Search query
            document_id: Optional document ID to restrict search
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        return self.search_engine.search(query, document_id, top_k)
    
    def get_document_outline(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get the hierarchical outline of a document
        
        Args:
            document_id: Document ID
            
        Returns:
            Hierarchical outline structure
        """
        return self.navigator.get_document_outline(document_id)
    
    def get_node_context(self, node_id: str) -> Dict[str, Any]:
        """
        Get navigation context for a node
        
        Args:
            node_id: Node ID
            
        Returns:
            Navigation context including parent, children, siblings
        """
        return self.navigator.get_navigation_context(node_id)
    
    def get_related_sections(self, node_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find sections related to the given node
        
        Args:
            node_id: Node ID
            top_k: Number of related sections to return
            
        Returns:
            List of related sections
        """
        node = self.db_connector.get_node_by_id(node_id)
        if not node:
            return []
        
        tree = self.db_connector.get_document_tree(node.document_id)
        if not tree:
            return []
        
        return self.search_engine.find_related_sections(node, tree, top_k)
    
    def navigate_to_parent(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to parent node"""
        return self.navigator.navigate_to_parent(node_id)
    
    def navigate_to_children(self, node_id: str) -> List[DocumentNode]:
        """Navigate to child nodes"""
        return self.navigator.navigate_to_children(node_id)
    
    def navigate_to_next_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to next sibling"""
        return self.navigator.navigate_to_next_sibling(node_id)
    
    def navigate_to_previous_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to previous sibling"""
        return self.navigator.navigate_to_previous_sibling(node_id)
    
    def get_document_stats(self, document_id: str) -> Dict[str, Any]:
        """
        Get statistics about a document
        
        Args:
            document_id: Document ID
            
        Returns:
            Document statistics
        """
        tree = self.db_connector.get_document_tree(document_id)
        if not tree:
            return {}
        
        tree_stats = tree.get_tree_stats()
        summary_stats = self.summarizer.get_summary_stats(tree)
        embedding_stats = self.embedding_generator.get_embedding_stats(tree)
        
        return {
            "document_id": document_id,
            "title": tree.document_title,
            "tree_stats": tree_stats,
            "summary_stats": summary_stats,
            "embedding_stats": embedding_stats
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the system"""
        return self.db_connector.get_all_documents()
    
    def delete_document(self, document_id: str) -> None:
        """Delete a document and all its data"""
        self.db_connector.delete_document_tree(document_id)
    
    def close(self):
        """Close database connections"""
        self.db_connector.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()