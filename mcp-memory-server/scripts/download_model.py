#!/usr/bin/env python3
"""
Pre-download and cache the sentence-transformers model for faster MCP server startup.
"""

import os
import time
from sentence_transformers import SentenceTransformer

def download_model():
    """Download and cache the embedding model."""
    model_name = "all-MiniLM-L6-v2"
    
    print(f"🚀 Pre-downloading model: {model_name}")
    print("This may take a few minutes on first run...")
    
    start_time = time.time()
    
    # Download and cache the model
    model = SentenceTransformer(
        model_name,
        device='cpu',
        cache_folder=os.path.expanduser("~/.cache/torch/sentence_transformers")
    )
    
    # Test encoding to ensure everything works
    print("🧪 Testing model...")
    test_embedding = model.encode(["test sentence"], show_progress_bar=False)
    
    download_time = time.time() - start_time
    
    print(f"✅ Model downloaded and cached successfully!")
    print(f"📊 Vector dimension: {test_embedding.shape[1]}")
    print(f"⏱️  Download time: {download_time:.2f} seconds")
    print(f"📁 Cache location: {model.cache_folder}")
    print(f"💾 Model size on disk: ~{get_model_size(model.cache_folder, model_name):.1f} MB")
    
    # Test load speed from cache
    print("\n🔄 Testing load speed from cache...")
    start_time = time.time()
    
    # Load again (should be much faster from cache)
    cached_model = SentenceTransformer(model_name, device='cpu')
    cached_model.encode(["test"], show_progress_bar=False)
    
    cache_load_time = time.time() - start_time
    print(f"⚡ Cache load time: {cache_load_time:.2f} seconds")
    
    print("\n🎉 Your MCP server will now start much faster!")

def get_model_size(cache_folder, model_name):
    """Get approximate model size in MB."""
    try:
        model_path = os.path.join(cache_folder, model_name.replace("/", "_"))
        if os.path.exists(model_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(model_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size / (1024 * 1024)  # Convert to MB
    except:
        pass
    return 0

if __name__ == "__main__":
    download_model()
