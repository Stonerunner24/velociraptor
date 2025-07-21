import os
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv

from ..models import DocumentNode, DocumentTree

load_dotenv()

class Neo4jConnector:
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        self.driver = None
        self.connect()
    
    def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("Connected to Neo4j database")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    def create_indexes(self):
        """Create necessary indexes for performance"""
        with self.driver.session() as session:
            # Create indexes
            session.run("CREATE INDEX IF NOT EXISTS FOR (n:DocumentNode) ON n.id")
            session.run("CREATE INDEX IF NOT EXISTS FOR (n:DocumentNode) ON n.document_id")
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Document) ON d.id")
    
    def store_document_tree(self, tree: DocumentTree) -> None:
        """Store the entire document tree in Neo4j"""
        with self.driver.session() as session:
            # Create document node
            session.run("""
                MERGE (d:Document {id: $document_id})
                SET d.title = $title,
                    d.root_node_id = $root_node_id,
                    d.created_at = datetime(),
                    d.updated_at = datetime()
            """, document_id=tree.document_id, 
                title=tree.document_title,
                root_node_id=tree.root_node_id)
            
            # Store all nodes
            for node in tree.nodes.values():
                self.store_node(node, session)
            
            # Create relationships
            for node in tree.nodes.values():
                if node.parent_id:
                    session.run("""
                        MATCH (parent:DocumentNode {id: $parent_id})
                        MATCH (child:DocumentNode {id: $child_id})
                        MERGE (parent)-[:HAS_CHILD]->(child)
                        MERGE (child)-[:CHILD_OF]->(parent)
                    """, parent_id=node.parent_id, child_id=node.id)
                
                # Connect to document
                session.run("""
                    MATCH (d:Document {id: $document_id})
                    MATCH (n:DocumentNode {id: $node_id})
                    MERGE (d)-[:CONTAINS]->(n)
                """, document_id=tree.document_id, node_id=node.id)
    
    def store_node(self, node: DocumentNode, session=None) -> None:
        """Store a single node in Neo4j"""
        if session is None:
            with self.driver.session() as session:
                self._store_node_query(session, node)
        else:
            self._store_node_query(session, node)
    
    def _store_node_query(self, session, node: DocumentNode):
        """Internal method to execute node storage query"""
        import json
        
        # Convert metadata dict to JSON string for Neo4j storage
        metadata_json = json.dumps(node.metadata) if node.metadata else "{}"
        
        session.run("""
            MERGE (n:DocumentNode {id: $id})
            SET n.content = $content,
                n.summary = $summary,
                n.embedding = $embedding,
                n.node_type = $node_type,
                n.parent_id = $parent_id,
                n.children_ids = $children_ids,
                n.document_id = $document_id,
                n.level = $level,
                n.page_start = $page_start,
                n.page_end = $page_end,
                n.metadata = $metadata,
                n.updated_at = datetime()
        """, 
            id=node.id,
            content=node.content,
            summary=node.summary,
            embedding=node.embedding,
            node_type=node.node_type.value,
            parent_id=node.parent_id,
            children_ids=node.children_ids,
            document_id=node.document_id,
            level=node.level,
            page_start=node.page_start,
            page_end=node.page_end,
            metadata=metadata_json
        )
    
    def get_document_tree(self, document_id: str) -> Optional[DocumentTree]:
        """Retrieve a document tree from Neo4j"""
        with self.driver.session() as session:
            # Get document info
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.title as title, d.root_node_id as root_node_id
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                return None
            
            # Get all nodes for this document
            nodes_result = session.run("""
                MATCH (d:Document {id: $document_id})-[:CONTAINS]->(n:DocumentNode)
                RETURN n
            """, document_id=document_id)
            
            # Create tree
            tree = DocumentTree(document_id, record["title"])
            tree.root_node_id = record["root_node_id"]
            
            # Add nodes to tree
            for record in nodes_result:
                node_data = dict(record["n"])
                node = self._create_node_from_data(node_data)
                tree.nodes[node.id] = node
            
            return tree
    
    def _create_node_from_data(self, data: Dict[str, Any]) -> DocumentNode:
        """Create DocumentNode from Neo4j data"""
        from ..models import NodeType
        
        return DocumentNode(
            id=data["id"],
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            embedding=data.get("embedding"),
            node_type=NodeType(data["node_type"]),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            document_id=data["document_id"],
            level=data.get("level", 0),
            page_start=data.get("page_start"),
            page_end=data.get("page_end"),
            metadata=data.get("metadata", {})
        )
    
    def search_nodes_by_similarity(self, query_embedding: List[float], 
                                  document_id: str = None,
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for nodes by embedding similarity"""
        # Note: This is a simplified version. For production, consider using vector search plugins
        with self.driver.session() as session:
            query = """
                MATCH (n:DocumentNode)
                WHERE n.embedding IS NOT NULL
            """
            
            if document_id:
                query += " AND n.document_id = $document_id"
            
            query += """
                RETURN n, n.embedding as embedding
                LIMIT $limit
            """
            
            result = session.run(query, 
                               document_id=document_id, 
                               limit=top_k * 2)  # Get more to compute similarity
            
            # Compute similarities in Python (for production, use vector search)
            nodes_with_similarity = []
            for record in result:
                node_data = dict(record["n"])
                node_embedding = record["embedding"]
                
                if node_embedding:
                    similarity = self._compute_cosine_similarity(query_embedding, node_embedding)
                    nodes_with_similarity.append({
                        "node": self._create_node_from_data(node_data),
                        "similarity": similarity
                    })
            
            # Sort by similarity and return top k
            nodes_with_similarity.sort(key=lambda x: x["similarity"], reverse=True)
            return nodes_with_similarity[:top_k]
    
    def _compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        import numpy as np
        
        if not vec1 or not vec2:
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_node_by_id(self, node_id: str) -> Optional[DocumentNode]:
        """Get a single node by ID"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:DocumentNode {id: $node_id})
                RETURN n
            """, node_id=node_id)
            
            record = result.single()
            if record:
                return self._create_node_from_data(dict(record["n"]))
            return None
    
    def delete_document_tree(self, document_id: str) -> None:
        """Delete a document and all its nodes"""
        with self.driver.session() as session:
            # Delete all relationships and nodes
            session.run("""
                MATCH (d:Document {id: $document_id})-[:CONTAINS]->(n:DocumentNode)
                DETACH DELETE n
            """, document_id=document_id)
            
            # Delete document
            session.run("""
                MATCH (d:Document {id: $document_id})
                DELETE d
            """, document_id=document_id)
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                RETURN d.id as id, d.title as title, d.created_at as created_at
                ORDER BY d.created_at DESC
            """)
            
            return [dict(record) for record in result]