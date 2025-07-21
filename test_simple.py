#!/usr/bin/env python3
"""
Simple test of Velociraptor components without processing large documents
"""

import os
from src.ai.embeddings import EmbeddingGenerator
from src.ai.summarizer import DocumentSummarizer

def test_embeddings():
    print("Testing embeddings...")
    try:
        generator = EmbeddingGenerator()
        
        # Test with a simple sentence
        text = "This is a test sentence for embedding generation."
        embedding = generator.generate_embedding(text)
        
        if embedding:
            print(f"✅ Embedding generated successfully! Dimension: {len(embedding)}")
        else:
            print("❌ Failed to generate embedding")
            
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")

def test_summarizer():
    print("\nTesting summarizer...")
    
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set - skipping summarizer test")
        return
    
    try:
        summarizer = DocumentSummarizer()
        
        # Test with a simple text
        text = """
        This is a sample document about machine learning. 
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        that can learn from data. It includes supervised learning, unsupervised learning, 
        and reinforcement learning approaches.
        """
        
        summary = summarizer.summarize_content(text)
        
        if summary and not summary.startswith("Summary unavailable"):
            print(f"✅ Summary generated successfully!")
            print(f"Summary: {summary}")
        else:
            print(f"❌ Failed to generate summary: {summary}")
            
    except Exception as e:
        print(f"❌ Summarizer test failed: {e}")

def main():
    print("=== Simple Velociraptor Component Tests ===")
    
    test_embeddings()
    test_summarizer()
    
    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    main()