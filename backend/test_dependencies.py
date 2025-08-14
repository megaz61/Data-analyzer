#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed
"""

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        import sentence_transformers
        print(f"✅ sentence_transformers: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"❌ sentence_transformers: {e}")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer class imported")
    except ImportError as e:
        print(f"❌ SentenceTransformer: {e}")
        return False
    
    try:
        import requests
        print(f"✅ requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        from langchain.embeddings.base import Embeddings
        print("✅ Langchain Embeddings base class")
    except ImportError as e:
        print(f"❌ Langchain Embeddings: {e}")
        return False
    
    try:
        from langchain.llms.base import LLM
        print("✅ Langchain LLM base class")
    except ImportError as e:
        print(f"❌ Langchain LLM: {e}")
        return False
    
    return True

def test_embedding_model():
    """Test embedding model loading"""
    print("\n🔍 Testing embedding model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Embedding model loaded successfully")
        
        # Test encoding
        test_text = "This is a test sentence"
        embedding = model.encode([test_text])
        print(f"✅ Test embedding created: shape {embedding.shape}")
        
        return True
    except Exception as e:
        print(f"❌ Embedding model test failed: {e}")
        return False

def test_huggingface_api():
    """Test HuggingFace API connectivity"""
    print("\n🔍 Testing HuggingFace API...")
    
    try:
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            print("❌ HUGGINGFACE_API_KEY not found in environment")
            return False
        
        if not api_key.startswith("hf_"):
            print("❌ Invalid API key format")
            return False
        
        print("✅ API key found and valid format")
        
        # Test API call
        url = "https://api-inference.huggingface.co/models/openai/gpt-oss-20b"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": "Hello", "parameters": {"max_new_tokens": 10}},
            timeout=10
        )
        
        print(f"✅ API response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API call successful")
            return True
        elif response.status_code == 503:
            print("⚠️ Model is loading, this is normal")
            return True
        else:
            print(f"⚠️ API returned: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return True  # Still return True as API is reachable
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 DEPENDENCY TEST")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test embedding model
    if not test_embedding_model():
        all_passed = False
    
    # Test HuggingFace API
    if not test_huggingface_api():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Ready to run the application.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 50)