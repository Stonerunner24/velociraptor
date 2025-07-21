#!/usr/bin/env python3
"""
Example usage of the Velociraptor Enterprise RAG system
"""

from src import Velociraptor

def main():
    # Initialize Velociraptor
    # Make sure to set your environment variables or pass them directly
    print("Initializing Velociraptor...")
    
    with Velociraptor(max_chunk_size=10) as raptor:
        
        # Example 1: Process a document
        print("\n=== Processing Document ===")
        try:
            # Replace with actual PDF path
            pdf_path = "banking_doc.pdf"
            document_id = raptor.process_document(pdf_path, "Banking Doc")
            print(f"Document processed with ID: {document_id}")
            
            # Get document statistics
            stats = raptor.get_document_stats(document_id)
            print(f"Document stats: {stats}")
            
        except FileNotFoundError:
            print("PDF file not found. Please provide a valid PDF path.")
            print("Continuing with search examples using existing documents...")
        
        # Example 2: List existing documents
        print("\n=== Listing Documents ===")
        documents = raptor.list_documents()
        print(f"Found {len(documents)} documents:")
        for doc in documents:
            print(f"  - {doc['title']} (ID: {doc['id']})")
        
        if not documents:
            print("No documents found. Please process a document first.")
            return
        
        # Use the first document for examples
        document_id = documents[0]['id']
        print(f"\nUsing document: {documents[0]['title']}")
        
        # Example 3: Search for content
        print("\n=== Semantic Search ===")
        search_queries = [
            "warfare",
            "messaging", 
            "science"
        ]
        
        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            results = raptor.search(query, document_id=document_id, top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['page_range']} (similarity: {result['similarity']:.3f})")
                    print(f"     Preview: {result['preview'][:100]}...")
            else:
                print("  No results found")
        
        # Example 4: Document outline
        print("\n=== Document Outline ===")
        outline = raptor.get_document_outline(document_id)
        print_outline(outline)
        
        # Example 5: Navigation
        if outline:
            print("\n=== Navigation Example ===")
            # Get the first node for navigation example
            first_node_id = outline[0]['id'] if outline else None
            
            if first_node_id:
                print(f"Starting from node: {first_node_id}")
                
                # Get navigation context
                context = raptor.get_node_context(first_node_id)
                print(f"Current node: {context['current']['page_range']}")
                print(f"Summary: {context['current']['summary'][:100]}...")
                
                # Show children
                if context['children']:
                    print(f"Children ({len(context['children'])}):")
                    for child in context['children']:
                        print(f"  - {child['page_range']}: {child['summary'][:50]}...")
                
                # Navigate to first child if available
                if context['children']:
                    child_id = context['children'][0]['id']
                    print(f"\nNavigating to child: {child_id}")
                    
                    # Get related sections
                    related = raptor.get_related_sections(child_id, top_k=2)
                    if related:
                        print("Related sections:")
                        for rel in related:
                            print(f"  - {rel['page_range']} (similarity: {rel['similarity']:.3f})")
                            print(f"    {rel['preview'][:50]}...")
        
        print("\n=== Example Complete ===")

def print_outline(outline, indent=0):
    """Print hierarchical outline"""
    for item in outline:
        prefix = "  " * indent
        print(f"{prefix}- {item['page_range']}: {item['summary'][:50]}...")
        
        if item['children']:
            print_outline(item['children'], indent + 1)

if __name__ == "__main__":
    main()