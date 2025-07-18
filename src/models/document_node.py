from typing import List, Optional, Dict, Any
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum

class NodeType(Enum):
    ROOT = "root"
    BRANCH = "branch"
    LEAF = "leaf"

@dataclass
class DocumentNode:
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    summary: str = ""
    embedding: Optional[List[float]] = None
    node_type: NodeType = NodeType.LEAF
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    document_id: str = ""
    level: int = 0
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child_node: 'DocumentNode') -> None:
        """Add a child node to this node"""
        if child_node.id not in self.children_ids:
            self.children_ids.append(child_node.id)
            child_node.parent_id = self.id
            child_node.level = self.level + 1
            
            # Update node type based on children
            if self.node_type == NodeType.LEAF and len(self.children_ids) > 0:
                self.node_type = NodeType.BRANCH
    
    def is_leaf(self) -> bool:
        """Check if this node is a leaf node"""
        return len(self.children_ids) == 0
    
    def is_root(self) -> bool:
        """Check if this node is the root node"""
        return self.parent_id is None
    
    def get_page_range(self) -> str:
        """Get formatted page range string"""
        if self.page_start is None:
            return "N/A"
        if self.page_end is None or self.page_start == self.page_end:
            return f"Page {self.page_start}"
        return f"Pages {self.page_start}-{self.page_end}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for storage"""
        return {
            "id": self.id,
            "content": self.content,
            "summary": self.summary,
            "embedding": self.embedding,
            "node_type": self.node_type.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "document_id": self.document_id,
            "level": self.level,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentNode':
        """Create node from dictionary"""
        node = cls(
            id=data["id"],
            content=data["content"],
            summary=data["summary"],
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
        return node