from typing import List, Dict, Any, Optional, Tuple
from ..models import DocumentNode, DocumentTree
from ..ai import EmbeddingGenerator
from ..database import Neo4jConnector

class SemanticSearchEngine:
    def __init__(self, embedding_generator: EmbeddingGenerator, 
                 db_connector: Neo4jConnector):
        self.embedding_generator = embedding_generator
        self.db_connector = db_connector
    
    def search(self, query: str, 
               document_id: Optional[str] = None,
               top_k: int = 5,
               threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for nodes semantically similar to the query
        
        Args:
            query: Search query text
            document_id: Optional document ID to restrict search
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results with node and similarity score
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        if not query_embedding:
            return []
        
        # Search in database
        results = self.db_connector.search_nodes_by_similarity(
            query_embedding, document_id, top_k * 2
        )
        
        # Filter by threshold and format results
        filtered_results = []
        for result in results:
            if result["similarity"] >= threshold:
                filtered_results.append({
                    "node": result["node"],
                    "similarity": result["similarity"],
                    "page_range": result["node"].get_page_range(),
                    "preview": self._generate_preview(result["node"])
                })
        
        return filtered_results[:top_k]
    
    def search_in_tree(self, query: str, tree: DocumentTree,
                      top_k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search within a specific document tree (in-memory)
        
        Args:
            query: Search query text
            tree: Document tree to search within
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results with node and similarity score
        """
        # Use embedding generator to search in tree
        results = self.embedding_generator.search_by_text(
            query, tree, top_k, threshold
        )
        
        # Format results
        formatted_results = []
        for node, similarity in results:
            formatted_results.append({
                "node": node,
                "similarity": similarity,
                "page_range": node.get_page_range(),
                "preview": self._generate_preview(node)
            })
        
        return formatted_results
    
    def _generate_preview(self, node: DocumentNode, max_length: int = 200) -> str:
        """Generate a preview of the node content"""
        text = node.summary if node.summary else node.content
        
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # If we can break on a word boundary
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    def get_context_for_node(self, node: DocumentNode, 
                           tree: DocumentTree) -> Dict[str, Any]:
        """
        Get contextual information around a node
        
        Args:
            node: The target node
            tree: Document tree containing the node
            
        Returns:
            Dictionary with context information
        """
        context = {
            "current_node": {
                "id": node.id,
                "summary": node.summary,
                "page_range": node.get_page_range(),
                "level": node.level
            },
            "parent": None,
            "children": [],
            "siblings": [],
            "path_to_root": []
        }
        
        # Get parent context
        parent = tree.get_parent(node.id)
        if parent:
            context["parent"] = {
                "id": parent.id,
                "summary": parent.summary,
                "page_range": parent.get_page_range()
            }
        
        # Get children context
        children = tree.get_children(node.id)
        for child in children:
            context["children"].append({
                "id": child.id,
                "summary": child.summary,
                "page_range": child.get_page_range()
            })
        
        # Get siblings context
        siblings = tree.get_siblings(node.id)
        for sibling in siblings:
            context["siblings"].append({
                "id": sibling.id,
                "summary": sibling.summary,
                "page_range": sibling.get_page_range()
            })
        
        # Get path to root
        path = tree.get_path_to_root(node.id)
        for path_node in path:
            context["path_to_root"].append({
                "id": path_node.id,
                "summary": path_node.summary,
                "level": path_node.level
            })
        
        return context
    
    def find_related_sections(self, node: DocumentNode, 
                            tree: DocumentTree,
                            top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find sections related to the given node based on content similarity
        
        Args:
            node: The reference node
            tree: Document tree to search within
            top_k: Number of related sections to return
            
        Returns:
            List of related sections with similarity scores
        """
        if not node.embedding:
            return []
        
        # Find similar nodes in the tree
        similar_nodes = self.embedding_generator.find_similar_nodes(
            node.embedding, tree, top_k * 2, threshold=0.5
        )
        
        # Filter out the node itself and format results
        related_sections = []
        for similar_node, similarity in similar_nodes:
            if similar_node.id != node.id:
                related_sections.append({
                    "node": similar_node,
                    "similarity": similarity,
                    "page_range": similar_node.get_page_range(),
                    "preview": self._generate_preview(similar_node)
                })
        
        return related_sections[:top_k]
    
    def explain_search_results(self, query: str, 
                             results: List[Dict[str, Any]]) -> str:
        """
        Generate an explanation of why these results were returned
        
        Args:
            query: Original search query
            results: Search results to explain
            
        Returns:
            Explanation text
        """
        if not results:
            return f"No results found for query: '{query}'"
        
        explanation = f"Found {len(results)} results for query: '{query}'\n\n"
        
        for i, result in enumerate(results, 1):
            node = result["node"]
            similarity = result["similarity"]
            page_range = result["page_range"]
            
            explanation += f"{i}. {page_range} (similarity: {similarity:.3f})\n"
            explanation += f"   Preview: {result['preview']}\n\n"
        
        return explanation