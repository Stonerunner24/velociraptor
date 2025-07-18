import os
from typing import List, Optional
import openai
import numpy as np
from dotenv import load_dotenv

from ..models import DocumentNode, DocumentTree

load_dotenv()

class EmbeddingGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-ada-002"):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model
        self.embedding_dimension = 1536  # Default for ada-002
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for the given text"""
        if not text.strip():
            return None
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_for_tree(self, tree: DocumentTree) -> None:
        """Generate embeddings for all leaf nodes in the tree"""
        leaf_nodes = tree.get_leaf_nodes()
        
        for node in leaf_nodes:
            self.generate_embedding_for_node(node)
    
    def generate_embedding_for_node(self, node: DocumentNode) -> None:
        """Generate embedding for a single node"""
        # Use summary if available, otherwise use content
        text_to_embed = node.summary if node.summary else node.content
        
        if text_to_embed:
            node.embedding = self.generate_embedding(text_to_embed)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_nodes(self, query_embedding: List[float], 
                          tree: DocumentTree, 
                          top_k: int = 5,
                          threshold: float = 0.7) -> List[tuple]:
        """Find nodes most similar to the query embedding"""
        if not query_embedding:
            return []
        
        similarities = []
        
        for node in tree.nodes.values():
            if node.embedding:
                similarity = self.compute_similarity(query_embedding, node.embedding)
                if similarity >= threshold:
                    similarities.append((node, similarity))
        
        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def search_by_text(self, query: str, tree: DocumentTree, 
                      top_k: int = 5, threshold: float = 0.7) -> List[tuple]:
        """Search for nodes similar to the query text"""
        query_embedding = self.generate_embedding(query)
        
        if not query_embedding:
            return []
        
        return self.find_similar_nodes(query_embedding, tree, top_k, threshold)
    
    def get_embedding_stats(self, tree: DocumentTree) -> dict:
        """Get statistics about embeddings in the tree"""
        total_nodes = len(tree.nodes)
        nodes_with_embeddings = sum(1 for node in tree.nodes.values() if node.embedding)
        leaf_nodes = len(tree.get_leaf_nodes())
        leaves_with_embeddings = sum(1 for node in tree.get_leaf_nodes() if node.embedding)
        
        return {
            "total_nodes": total_nodes,
            "nodes_with_embeddings": nodes_with_embeddings,
            "leaf_nodes": leaf_nodes,
            "leaves_with_embeddings": leaves_with_embeddings,
            "leaf_completion_rate": leaves_with_embeddings / leaf_nodes if leaf_nodes > 0 else 0
        }
    
    def regenerate_embedding(self, node: DocumentNode) -> None:
        """Regenerate embedding for a specific node"""
        self.generate_embedding_for_node(node)