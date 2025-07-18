import os
from typing import List, Optional
import openai
from dotenv import load_dotenv

from ..models import DocumentNode, DocumentTree

load_dotenv()

class DocumentSummarizer:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model
    
    def summarize_content(self, content: str, context: str = "") -> str:
        """Generate a summary for the given content"""
        if not content.strip():
            return ""
        
        prompt = f"""Please provide a concise summary of the following content.
        
{f"Context: {context}" if context else ""}

Content:
{content}

Summary:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, informative summaries of document content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Summary unavailable: {str(e)}"
    
    def summarize_child_summaries(self, child_summaries: List[str], page_range: str = "") -> str:
        """Generate a summary from child node summaries"""
        if not child_summaries:
            return ""
        
        combined_summaries = "\n\n".join(child_summaries)
        
        prompt = f"""Please create a cohesive summary that synthesizes the following section summaries:

{f"Page range: {page_range}" if page_range else ""}

Section summaries:
{combined_summaries}

Synthesized summary:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates cohesive summaries by synthesizing information from multiple sections."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating summary from child summaries: {e}")
            return f"Summary unavailable: {str(e)}"
    
    def generate_summaries_for_tree(self, tree: DocumentTree) -> None:
        """Generate summaries for all nodes in the tree, bottom-up"""
        if not tree.nodes:
            return
        
        # Get all nodes sorted by level (highest level first for bottom-up processing)
        nodes_by_level = {}
        max_level = 0
        
        for node in tree.nodes.values():
            if node.level not in nodes_by_level:
                nodes_by_level[node.level] = []
            nodes_by_level[node.level].append(node)
            max_level = max(max_level, node.level)
        
        # Process nodes from highest level (leaves) to lowest level (root)
        for level in range(max_level, -1, -1):
            if level not in nodes_by_level:
                continue
                
            for node in nodes_by_level[level]:
                self.generate_summary_for_node(node, tree)
    
    def generate_summary_for_node(self, node: DocumentNode, tree: DocumentTree) -> None:
        """Generate summary for a single node"""
        if node.is_leaf():
            # For leaf nodes, summarize the content directly
            context = f"This is part of a document (pages {node.get_page_range()})"
            node.summary = self.summarize_content(node.content, context)
        else:
            # For parent nodes, summarize child summaries
            children = tree.get_children(node.id)
            if children:
                child_summaries = [child.summary for child in children if child.summary]
                page_range = node.get_page_range()
                node.summary = self.summarize_child_summaries(child_summaries, page_range)
            else:
                node.summary = "No content available"
    
    def regenerate_summary(self, node: DocumentNode, tree: DocumentTree) -> None:
        """Regenerate summary for a specific node"""
        self.generate_summary_for_node(node, tree)
    
    def get_summary_stats(self, tree: DocumentTree) -> dict:
        """Get statistics about summaries in the tree"""
        total_nodes = len(tree.nodes)
        nodes_with_summaries = sum(1 for node in tree.nodes.values() if node.summary)
        
        return {
            "total_nodes": total_nodes,
            "nodes_with_summaries": nodes_with_summaries,
            "completion_rate": nodes_with_summaries / total_nodes if total_nodes > 0 else 0
        }