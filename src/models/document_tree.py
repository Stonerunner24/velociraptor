from typing import Dict, List, Optional, Any
from .document_node import DocumentNode, NodeType

class DocumentTree:
    def __init__(self, document_id: str, document_title: str = ""):
        self.document_id = document_id
        self.document_title = document_title
        self.nodes: Dict[str, DocumentNode] = {}
        self.root_node_id: Optional[str] = None
    
    def add_node(self, node: DocumentNode) -> None:
        """Add a node to the tree"""
        self.nodes[node.id] = node
        
        # Set as root if it's the first node or explicitly a root
        if self.root_node_id is None or node.is_root():
            self.root_node_id = node.id
            node.node_type = NodeType.ROOT
    
    def get_node(self, node_id: str) -> Optional[DocumentNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_root_node(self) -> Optional[DocumentNode]:
        """Get the root node"""
        if self.root_node_id:
            return self.nodes.get(self.root_node_id)
        return None
    
    def get_children(self, node_id: str) -> List[DocumentNode]:
        """Get all children of a node"""
        node = self.get_node(node_id)
        if not node:
            return []
        
        return [self.nodes[child_id] for child_id in node.children_ids 
                if child_id in self.nodes]
    
    def get_parent(self, node_id: str) -> Optional[DocumentNode]:
        """Get the parent of a node"""
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return None
        
        return self.nodes.get(node.parent_id)
    
    def get_siblings(self, node_id: str) -> List[DocumentNode]:
        """Get all siblings of a node"""
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return []
        
        parent = self.get_parent(node_id)
        if not parent:
            return []
        
        return [self.nodes[child_id] for child_id in parent.children_ids 
                if child_id in self.nodes and child_id != node_id]
    
    def get_leaf_nodes(self) -> List[DocumentNode]:
        """Get all leaf nodes in the tree"""
        return [node for node in self.nodes.values() if node.is_leaf()]
    
    def get_path_to_root(self, node_id: str) -> List[DocumentNode]:
        """Get the path from a node to the root"""
        path = []
        current_node = self.get_node(node_id)
        
        while current_node:
            path.append(current_node)
            if current_node.parent_id:
                current_node = self.get_node(current_node.parent_id)
            else:
                break
        
        return path
    
    def get_next_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Get the next sibling node"""
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return None
        
        parent = self.get_parent(node_id)
        if not parent:
            return None
        
        try:
            current_index = parent.children_ids.index(node_id)
            if current_index + 1 < len(parent.children_ids):
                next_sibling_id = parent.children_ids[current_index + 1]
                return self.nodes.get(next_sibling_id)
        except ValueError:
            pass
        
        return None
    
    def get_previous_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Get the previous sibling node"""
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return None
        
        parent = self.get_parent(node_id)
        if not parent:
            return None
        
        try:
            current_index = parent.children_ids.index(node_id)
            if current_index > 0:
                prev_sibling_id = parent.children_ids[current_index - 1]
                return self.nodes.get(prev_sibling_id)
        except ValueError:
            pass
        
        return None
    
    def get_tree_stats(self) -> Dict[str, Any]:
        """Get statistics about the tree"""
        leaf_nodes = self.get_leaf_nodes()
        max_level = max((node.level for node in self.nodes.values()), default=0)
        
        return {
            "total_nodes": len(self.nodes),
            "leaf_nodes": len(leaf_nodes),
            "max_depth": max_level,
            "document_id": self.document_id,
            "document_title": self.document_title
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary for storage"""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "root_node_id": self.root_node_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentTree':
        """Create tree from dictionary"""
        tree = cls(data["document_id"], data.get("document_title", ""))
        tree.root_node_id = data.get("root_node_id")
        
        for node_id, node_data in data.get("nodes", {}).items():
            node = DocumentNode.from_dict(node_data)
            tree.nodes[node_id] = node
        
        return tree