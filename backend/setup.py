#!/usr/bin/env python3
"""
Setup script untuk menginstall dan mengkonfigurasi dependencies NLP
untuk Enhanced AI Data Analysis API
"""

import subprocess
import sys
import os
import nltk
from pathlib import Path

def install_requirements():
    """Install semua requirements dari requirements.txt"""
    print("🔧 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def download_nltk_data():
    """Download NLTK data yang diperlukan"""
    print("📥 Downloading NLTK data...")
    try:
        # Download required NLTK data
        nltk_downloads = [
            'punkt',
            'stopwords', 
            'wordnet',
            'omw-1.4',
            'averaged_perceptron_tagger'
        ]
        
        for data in nltk_downloads:
            print(f"  Downloading {data}...")
            try:
                nltk.download(data, quiet=True)
                print(f"  ✅ {data} downloaded")
            except Exception as e:
                print(f"  ⚠️ Failed to download {data}: {e}")
        
        print("✅ NLTK data setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup NLTK data: {e}")
        return False

def create_nltk_data_dir():
    """Buat direktori untuk NLTK data jika belum ada"""
    try:
        nltk_data_dir = Path.home() / 'nltk_data'
        nltk_data_dir.mkdir(exist_ok=True)
        print(f"📁 NLTK data directory: {nltk_data_dir}")
        return True
    except Exception as e:
        print(f"❌ Failed to create NLTK data directory: {e}")
        return False

def verify_installation():
    """Verifikasi bahwa semua dependencies terinstall dengan benar"""
    print("🔍 Verifying installation...")
    
    # Test basic imports
    test_imports = [
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('sklearn', 'Machine learning'),
        ('nltk', 'Natural language processing'),
        ('sentence_transformers', 'Text embeddings'),
        ('google.generativeai', 'Google Gemini AI'),
        ('fastapi', 'Web framework'),
        ('PyPDF2', 'PDF processing')
    ]
    
    failed_imports = []
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError as e:
            print(f"  ❌ {module} - {description} - FAILED: {e}")
            failed_imports.append(module)
    
    # Test NLTK data
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        print("  ✅ NLTK data - Available")
    except LookupError:
        print("  ❌ NLTK data - Missing required data")
        failed_imports.append('nltk_data')
    
    if not failed_imports:
        print("✅ All dependencies verified successfully!")
        return True
    else:
        print(f"❌ Failed imports: {failed_imports}")
        return False

def test_nlp_features():
    """Test NLP features untuk memastikan berfungsi dengan baik"""
    print("🧪 Testing NLP features...")
    
    try:
        # Test TF-IDF
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=10)
        test_docs = ["This is a test document.", "Another test document with different words."]
        vectorizer.fit_transform(test_docs)
        print("  ✅ TF-IDF vectorization works")
        
        # Test NLTK tokenization
        from nltk.tokenize import sent_tokenize, word_tokenize
        test_text = "This is a test sentence. This is another sentence."
        sentences = sent_tokenize(test_text)
        words = word_tokenize(test_text)
        print(f"  ✅ NLTK tokenization works - {len(sentences)} sentences, {len(words)} words")
        
        # Test stopwords
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
        print(f"  ✅ Stopwords loaded - {len(stop_words)} English stopwords")
        
        # Test sentence transformers
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embedding = model.encode(["Test sentence"])
        print(f"  ✅ Sentence transformers works - embedding shape: {embedding.shape}")
        
        print("✅ All NLP features working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ NLP feature test failed: {e}")
        return False

def check_env_file():
    """Check dan beri informasi tentang .env file"""
    print("🔧 Checking environment configuration...")
    
    env_file = Path('.env')
    if env_file.exists():
        print("  ✅ .env file found")
        
        # Check for required variables
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        required_vars = ['GEMINI_API_KEY', 'GEMINI_MODEL_NAME']
        missing_vars = []
        
        for var in required_vars:
            if var not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"  ⚠️ Missing environment variables: {missing_vars}")
        else:
            print("  ✅ All required environment variables present")
    else:
        print("  ❌ .env file not found")
        print("  📝 Please create .env file with required variables:")
        print("     GEMINI_API_KEY=your_api_key_here")
        print("     GEMINI_MODEL_NAME=gemini-1.5-flash")

def main():
    """Main setup function"""
    print("🚀 Setting up Enhanced AI Data Analysis API")
    print("=" * 50)
    
    success_count = 0
    total_steps = 6
    
    # Step 1: Create NLTK data directory
    if create_nltk_data_dir():
        success_count += 1
    
    # Step 2: Install requirements
    if install_requirements():
        success_count += 1
    
    # Step 3: Download NLTK data
    if download_nltk_data():
        success_count += 1
    
    # Step 4: Verify installation
    if verify_installation():
        success_count += 1
    
    # Step 5: Test NLP features
    if test_nlp_features():
        success_count += 1
    
    # Step 6: Check environment
    check_env_file()
    success_count += 1  # Always increment as this is informational
    
    print("=" * 50)
    print(f"Setup completed: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 Setup completed successfully!")
        print("🚀 You can now run the API with: uvicorn main:app --reload")
    else:
        print("⚠️ Setup completed with some issues. Please check the errors above.")
        
    print("\n📚 Features available:")
    print("  • Enhanced CSV/Excel analysis with automatic type detection")
    print("  • PDF processing with NLP (keyword extraction, summarization)")
    print("  • Data quality assessment and recommendations")
    print("  • AI-powered chat with RAG using Google Gemini")
    print("  • Advanced data visualizations")

if __name__ == "__main__":
    main()