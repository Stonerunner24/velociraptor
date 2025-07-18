from typing import List, Dict, Any, Optional
from ..models import DocumentNode, DocumentTree
from ..database import Neo4jConnector

class TreeNavigator:
    def __init__(self, db_connector: Neo4jConnector):
        self.db_connector = db_connector
    
    def navigate_to_parent(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to the parent of the current node"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node or not node.parent_id:
            return None
        
        return self.db_connector.get_node_by_id(node.parent_id)
    
    def navigate_to_children(self, node_id: str) -> List[DocumentNode]:
        """Navigate to all children of the current node"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node:
            return []
        
        children = []
        for child_id in node.children_ids:
            child = self.db_connector.get_node_by_id(child_id)
            if child:
                children.append(child)
        
        return children
    
    def navigate_to_next_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to the next sibling node"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node or not node.parent_id:
            return None
        
        parent = self.db_connector.get_node_by_id(node.parent_id)
        if not parent:
            return None
        
        try:
            current_index = parent.children_ids.index(node_id)
            if current_index + 1 < len(parent.children_ids):
                next_sibling_id = parent.children_ids[current_index + 1]
                return self.db_connector.get_node_by_id(next_sibling_id)
        except ValueError:
            pass
        
        return None
    
    def navigate_to_previous_sibling(self, node_id: str) -> Optional[DocumentNode]:
        """Navigate to the previous sibling node"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node or not node.parent_id:
            return None
        
        parent = self.db_connector.get_node_by_id(node.parent_id)
        if not parent:
            return None
        
        try:
            current_index = parent.children_ids.index(node_id)
            if current_index > 0:
                prev_sibling_id = parent.children_ids[current_index - 1]
                return self.db_connector.get_node_by_id(prev_sibling_id)
        except ValueError:
            pass
        
        return None
    
    def get_breadcrumb_path(self, node_id: str) -> List[Dict[str, Any]]:
        """Get the breadcrumb path from root to current node"""
        path = []
        current_node = self.db_connector.get_node_by_id(node_id)
        
        while current_node:
            path.append({
                "id": current_node.id,
                "summary": current_node.summary or "Section",
                "page_range": current_node.get_page_range(),
                "level": current_node.level
            })
            
            if current_node.parent_id:
                current_node = self.db_connector.get_node_by_id(current_node.parent_id)
            else:
                break
        
        # Reverse to get root-to-current order
        path.reverse()
        return path
    
    def get_navigation_context(self, node_id: str) -> Dict[str, Any]:
        """Get complete navigation context for a node"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node:
            return {}
        
        context = {
            "current": {
                "id": node.id,
                "summary": node.summary,
                "page_range": node.get_page_range(),
                "level": node.level,
                "node_type": node.node_type.value
            },
            "parent": None,
            "children": [],
            "next_sibling": None,
            "previous_sibling": None,
            "breadcrumb_path": self.get_breadcrumb_path(node_id)
        }
        
        # Get parent
        parent = self.navigate_to_parent(node_id)
        if parent:
            context["parent"] = {
                "id": parent.id,
                "summary": parent.summary,
                "page_range": parent.get_page_range()
            }
        
        # Get children
        children = self.navigate_to_children(node_id)
        for child in children:
            context["children"].append({
                "id": child.id,
                "summary": child.summary,
                "page_range": child.get_page_range()
            })
        
        # Get next sibling
        next_sibling = self.navigate_to_next_sibling(node_id)
        if next_sibling:
            context["next_sibling"] = {
                "id": next_sibling.id,
                "summary": next_sibling.summary,
                "page_range": next_sibling.get_page_range()
            }
        
        # Get previous sibling
        prev_sibling = self.navigate_to_previous_sibling(node_id)
        if prev_sibling:
            context["previous_sibling"] = {
                "id": prev_sibling.id,
                "summary": prev_sibling.summary,
                "page_range": prev_sibling.get_page_range()
            }
        
        return context
    
    def find_next_leaf_node(self, node_id: str) -> Optional[DocumentNode]:
        """Find the next leaf node in document order"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node:
            return None
        
        # If current node has children, go to first child
        if node.children_ids:
            first_child = self.db_connector.get_node_by_id(node.children_ids[0])
            if first_child:
                # Recursively find first leaf in this subtree
                return self._find_first_leaf_in_subtree(first_child)
        
        # Otherwise, find next sibling or parent's next sibling
        current_node = node
        while current_node:
            next_sibling = self.navigate_to_next_sibling(current_node.id)
            if next_sibling:
                return self._find_first_leaf_in_subtree(next_sibling)
            
            # Go up to parent
            current_node = self.navigate_to_parent(current_node.id)
        
        return None
    
    def find_previous_leaf_node(self, node_id: str) -> Optional[DocumentNode]:
        """Find the previous leaf node in document order"""
        node = self.db_connector.get_node_by_id(node_id)
        if not node:
            return None
        
        # Find previous sibling
        prev_sibling = self.navigate_to_previous_sibling(node_id)
        if prev_sibling:
            return self._find_last_leaf_in_subtree(prev_sibling)
        
        # If no previous sibling, go to parent
        parent = self.navigate_to_parent(node_id)
        if parent and parent.is_leaf():
            return parent
        
        return None
    
    def _find_first_leaf_in_subtree(self, node: DocumentNode) -> Optional[DocumentNode]:
        """Find the first leaf node in a subtree"""
        if node.is_leaf():
            return node
        
        # Go to first child and recursively find first leaf
        if node.children_ids:
            first_child = self.db_connector.get_node_by_id(node.children_ids[0])
            if first_child:
                return self._find_first_leaf_in_subtree(first_child)
        
        return None
    
    def _find_last_leaf_in_subtree(self, node: DocumentNode) -> Optional[DocumentNode]:
        """Find the last leaf node in a subtree"""
        if node.is_leaf():
            return node
        
        # Go to last child and recursively find last leaf
        if node.children_ids:
            last_child = self.db_connector.get_node_by_id(node.children_ids[-1])
            if last_child:
                return self._find_last_leaf_in_subtree(last_child)
        
        return None
    
    def get_document_outline(self, document_id: str) -> List[Dict[str, Any]]:
        """Get a hierarchical outline of the document"""
        tree = self.db_connector.get_document_tree(document_id)
        if not tree:
            return []
        
        root = tree.get_root_node()
        if not root:
            return []
        
        return self._build_outline_recursive(root, tree)
    
    def _build_outline_recursive(self, node: DocumentNode, 
                                tree: DocumentTree) -> List[Dict[str, Any]]:
        """Recursively build outline structure"""
        outline_item = {
            "id": node.id,
            "summary": node.summary or "Section",
            "page_range": node.get_page_range(),
            "level": node.level,
            "children": []
        }
        
        # Add children
        children = tree.get_children(node.id)
        for child in children:
            child_outline = self._build_outline_recursive(child, tree)
            outline_item["children"].extend(child_outline)
        
        return [outline_item]