import PyPDF2
from typing import List, Dict, Any, Optional
from io import BytesIO
from uuid import uuid4

from ..models import DocumentNode, DocumentTree, NodeType

class DocumentSplitter:
    def __init__(self, 
                 max_chunk_size: int = 10,  # pages per chunk
                 min_chunk_size: int = 1,   # minimum pages per chunk
                 overlap_pages: int = 1):   # pages of overlap between chunks
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_pages = overlap_pages
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF, returning list of page data"""
        pages = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"PDF has {total_pages} pages")
            
            for page_num, page in enumerate(pdf_reader.pages):
                if page_num % 50 == 0:  # Progress update every 50 pages
                    print(f"Processing page {page_num + 1}/{total_pages}")
                
                try:
                    text = page.extract_text()
                    pages.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'char_count': len(text)
                    })
                except Exception as e:
                    print(f"Warning: Failed to extract text from page {page_num + 1}: {e}")
                    continue
        
        return pages
    
    def split_pages_into_chunks(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split pages into chunks based on max_chunk_size"""
        if not pages:
            return []
        
        chunks = []
        total_pages = len(pages)
        
        i = 0
        while i < total_pages:
            chunk_end = min(i + self.max_chunk_size, total_pages)
            print(f"chunk {i}: pages {i+1}-{chunk_end} (max_chunk_size: {self.max_chunk_size})")
            
            # Collect pages for this chunk
            chunk_pages = pages[i:chunk_end]
            
            # Combine text from all pages in chunk
            combined_text = '\n\n'.join([page['text'] for page in chunk_pages])
            
            chunk = {
                'page_start': chunk_pages[0]['page_number'],
                'page_end': chunk_pages[-1]['page_number'],
                'text': combined_text,
                'char_count': len(combined_text),
                'page_count': len(chunk_pages)
            }
            
            chunks.append(chunk)
            
            # Move to next chunk with overlap consideration
            i = max(i + 1, chunk_end - self.overlap_pages) if self.overlap_pages > 0 else chunk_end
        
        return chunks
    
    def create_leaf_nodes(self, chunks: List[Dict[str, Any]], document_id: str) -> List[DocumentNode]:
        """Create leaf nodes from chunks"""
        leaf_nodes = []
        
        for chunk in chunks:
            node = DocumentNode(
                id=str(uuid4()),
                content=chunk['text'],
                node_type=NodeType.LEAF,
                document_id=document_id,
                level=1,  # Leaf nodes are at level 1 (root is level 0)
                page_start=chunk['page_start'],
                page_end=chunk['page_end'],
                metadata={
                    'char_count': chunk['char_count'],
                    'page_count': chunk['page_count']
                }
            )
            leaf_nodes.append(node)
        
        return leaf_nodes
    
    def create_parent_nodes(self, child_nodes: List[DocumentNode], 
                           document_id: str, level: int) -> List[DocumentNode]:
        """Create parent nodes by grouping child nodes"""
        if len(child_nodes) <= 1:
            return child_nodes
        
        parent_nodes = []
        
        # Group children into parent nodes (e.g., every 3-5 children per parent)
        group_size = min(5, max(2, len(child_nodes) // 3))
        
        for i in range(0, len(child_nodes), group_size):
            group = child_nodes[i:i + group_size]
            
            # Create parent node
            parent_node = DocumentNode(
                id=str(uuid4()),
                content="",  # Will be filled with summary later
                node_type=NodeType.BRANCH,
                document_id=document_id,
                level=level,
                page_start=min(node.page_start for node in group if node.page_start),
                page_end=max(node.page_end for node in group if node.page_end),
                metadata={
                    'child_count': len(group),
                    'total_pages': sum(node.metadata.get('page_count', 1) for node in group)
                }
            )
            
            # Add children to parent
            for child in group:
                parent_node.add_child(child)
            
            parent_nodes.append(parent_node)
        
        return parent_nodes
    
    def build_tree_structure(self, leaf_nodes: List[DocumentNode], 
                           document_id: str) -> DocumentTree:
        """Build the complete tree structure from leaf nodes"""
        if not leaf_nodes:
            return DocumentTree(document_id)
        
        tree = DocumentTree(document_id)
        
        # Add all leaf nodes to tree
        for node in leaf_nodes:
            tree.add_node(node)
        
        # Build tree bottom-up
        current_level_nodes = leaf_nodes
        current_level = 1
        
        while len(current_level_nodes) > 1:
            # Create parent nodes for current level
            parent_nodes = self.create_parent_nodes(
                current_level_nodes, document_id, current_level
            )
            
            # Add parent nodes to tree
            for parent in parent_nodes:
                tree.add_node(parent)
            
            current_level_nodes = parent_nodes
            current_level += 1
        
        # Create root node if we have multiple top-level nodes
        if len(current_level_nodes) == 1:
            root_node = current_level_nodes[0]
            root_node.node_type = NodeType.ROOT
            root_node.level = 0
            tree.root_node_id = root_node.id
        else:
            # Create a single root node
            root_node = DocumentNode(
                id=str(uuid4()),
                content="",  # Will be filled with summary later
                node_type=NodeType.ROOT,
                document_id=document_id,
                level=0,
                page_start=min(node.page_start for node in current_level_nodes if node.page_start),
                page_end=max(node.page_end for node in current_level_nodes if node.page_end),
                metadata={
                    'child_count': len(current_level_nodes),
                    'is_synthetic_root': True
                }
            )
            
            # Add all current level nodes as children
            for child in current_level_nodes:
                root_node.add_child(child)
            
            tree.add_node(root_node)
            tree.root_node_id = root_node.id
        
        return tree
    
    def process_document(self, pdf_path: str, document_title: str = "") -> DocumentTree:
        """Main method to process a document and create tree structure"""
        document_id = str(uuid4())
        
        # Extract pages from PDF
        pages = self.extract_text_from_pdf(pdf_path)
        
        if not pages:
            return DocumentTree(document_id, document_title)
        
        print("splitting pages")
        # Split pages into chunks
        chunks = self.split_pages_into_chunks(pages)
        
        print("Creating nodes")
        # Create leaf nodes
        leaf_nodes = self.create_leaf_nodes(chunks, document_id)

        print("Building tree")
        
        # Build tree structure
        tree = self.build_tree_structure(leaf_nodes, document_id)
        tree.document_title = document_title
        
        return tree