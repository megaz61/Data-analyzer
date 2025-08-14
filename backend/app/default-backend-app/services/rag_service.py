import os
import json
import numpy as np
from typing import Dict, Any, List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from datetime import datetime

# Load environment variables
load_dotenv()

class GeminiRAGService:
    def __init__(self):
        # Check if Gemini API key is available
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not gemini_key:
            raise Exception("GEMINI_API_KEY not found in environment variables")
 
        self.api_key = gemini_key
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ Gemini model '{self.model_name}' initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini model: {e}")
            raise Exception(f"Failed to initialize Gemini model: {e}")
        
        print(f"DEBUG: Model Name from .env: {self.model_name}")
        print(f"DEBUG: API Key loaded (first 5 chars): {self.api_key[:5]}*****")
        
        # Initialize embedding model
        try:
            print("🔄 Loading embedding model...")
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            print("✅ Embedding model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            raise Exception(f"Failed to load embedding model: {e}")
        
        # Initialize storage
        self.vector_stores = {}
        self.memories = {}
        self.document_chunks = {}
        
        print(f"✅ Gemini RAG Service initialized successfully with {self.model_name}")
    
    def create_vector_store(self, file_data: Dict[str, Any]) -> str:
        """Create vector store from processed file data"""
        file_id = file_data['file_id']
        
        try:
            print(f"🔄 Creating vector store for file: {file_data.get('filename', 'Unknown')}")
            
            # Convert data to text chunks
            texts = self._extract_texts_from_data(file_data)
            
            if not texts:
                raise Exception("No text content found to create vector store")
            
            print(f"✅ Extracted {len(texts)} text chunks")
            
            # Split texts into manageable chunks
            chunks = self._split_texts(texts)
            print(f"✅ Created {len(chunks)} document chunks")
            
            # Create embeddings for all chunks
            print("🔄 Creating embeddings...")
            embeddings = []
            for chunk in chunks:
                embedding = self.embedding_model.encode(chunk)
                embeddings.append(embedding)
            
            embeddings = np.array(embeddings)
            print(f"✅ Created embeddings: {embeddings.shape}")
            
            # Store everything
            self.vector_stores[file_id] = {
                'embeddings': embeddings,
                'chunks': chunks,
                'metadata': {
                    'filename': file_data.get('filename'),
                    'file_type': file_data.get('type'),
                    'created_at': datetime.now().isoformat()
                }
            }
            
            self.memories[file_id] = []  # Chat history
            
            print("✅ Vector store created successfully")
            return file_id
            
        except Exception as e:
            print(f"❌ Error creating vector store: {str(e)}")
            raise Exception(f"Error creating vector store: {str(e)}")
    
    def query(self, file_id: str, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        if file_id not in self.vector_stores:
            raise Exception("File not found in RAG system")
        
        try:
            print(f"🔄 Processing query: {question[:50]}...")
            
            # Get relevant chunks
            relevant_chunks = self._retrieve_relevant_chunks(file_id, question)
            
            # Create context from relevant chunks
            context = "\n\n".join(relevant_chunks)
            
            # Get chat history
            chat_history = self.memories[file_id]
            history_text = ""
            if chat_history:
                history_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" 
                                        for item in chat_history[-3:]])
            
            # Create prompt
            prompt = self._create_prompt(context, history_text, question)
            
            # Get response from Gemini
            response = self._query_gemini(prompt)
            
            # Store in memory
            self.memories[file_id].append({
                'question': question,
                'answer': response,
                'timestamp': datetime.now().isoformat()
            })
            
            print("✅ Query processed successfully")
            
            return {
                "response": response,
                "sources": relevant_chunks[:3]  # Return top 3 relevant chunks as sources
            }
            
        except Exception as e:
            print(f"❌ Error querying RAG system: {str(e)}")
            raise Exception(f"Error querying RAG system: {str(e)}")
    
    def _retrieve_relevant_chunks(self, file_id: str, question: str, top_k: int = 3) -> List[str]:
        """Retrieve most relevant chunks for the question"""
        vector_store = self.vector_stores[file_id]
        embeddings = vector_store['embeddings']
        chunks = vector_store['chunks']
        
        # Create embedding for the question
        question_embedding = self.embedding_model.encode(question)
        
        # Calculate similarities
        similarities = np.dot(embeddings, question_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        # Get top k most similar chunks
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        relevant_chunks = [chunks[i] for i in top_indices]
        
        return relevant_chunks
    
    def _create_prompt(self, context: str, chat_history: str, question: str) -> str:
        """Create prompt for Gemini model"""
        prompt = f"""Anda adalah asisten AI analisis data yang membantu. 
Silakan analisis data berikut dan jawab pertanyaan pengguna dalam bahasa Indonesia.

Konteks Data:
{context[:2000]}

Riwayat Percakapan:
{chat_history}

Pertanyaan: {question}

Instruksi:
- Berikan jawaban yang detail dan akurat dalam bahasa Indonesia
- Jika jawaban tidak dapat ditemukan dalam konteks, katakan dengan jujur
- Gunakan data yang tersedia untuk memberikan insight yang berguna
- Format jawaban dengan jelas dan mudah dipahami

Jawaban:"""
        
        return prompt
    
    def _query_gemini(self, prompt: str) -> str:
        """Query Gemini API"""
        try:
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )
            
            # Safety settings (optional)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if response.candidates[0].finish_reason.name == "SAFETY":
                return "Maaf, respons tidak dapat dihasilkan karena alasan keamanan. Silakan coba pertanyaan lain."
            
            # Extract text from response
            generated_text = response.text.strip()
            return generated_text if generated_text else 'Maaf, tidak ada respons yang dihasilkan.'
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            if "quota" in str(e).lower():
                return "Maaf, kuota API Gemini telah habis. Silakan coba lagi nanti."
            elif "api key" in str(e).lower():
                return "Maaf, terjadi masalah dengan konfigurasi API key."
            else:
                return f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini AI: {str(e)}"
    
    def _split_texts(self, texts: List[str], chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
        """Split texts into smaller chunks"""
        chunks = []
        
        for text in texts:
            if len(text) <= chunk_size:
                chunks.append(text)
                continue
            
            # Split into chunks with overlap
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append(chunk)
                
                if end >= len(text):
                    break
                    
                start = end - chunk_overlap
        
        return chunks
    
    def _extract_texts_from_data(self, file_data: Dict[str, Any]) -> List[str]:
        """Extract text chunks from processed file data"""
        texts = []
        file_type = file_data.get('type')
        
        try:
            # Add file metadata
            metadata_text = f"Informasi File:\n- Nama: {file_data.get('filename')}\n- Tipe: {file_type}\n- ID: {file_data.get('file_id')}"
            texts.append(metadata_text)
            
            if file_type in ['pdf', 'docx', 'txt']:
                text = file_data.get('text', '')
                if text:
                    texts.append(f"Konten Dokumen:\n{text}")
                    
                    analysis = file_data.get('analysis', {})
                    if analysis:
                        analysis_text = f"Ringkasan Analisis File:\n{json.dumps(analysis, indent=2, ensure_ascii=False)}"
                        texts.append(analysis_text)
            
            elif file_type == 'csv':
                data = file_data.get('data', [])
                analysis = file_data.get('analysis', {})
                
                if data:
                    sample_data = data[:10]
                    data_text = f"Contoh Data CSV (10 baris pertama):\n{json.dumps(sample_data, indent=2, ensure_ascii=False)}"
                    texts.append(data_text)
                
                if analysis:
                    analysis_text = f"Analisis Data Detail:\n{json.dumps(analysis, indent=2, ensure_ascii=False)}"
                    texts.append(analysis_text)
                
                columns = analysis.get('columns', [])
                if columns:
                    column_text = f"Kolom Dataset:\n" + "\n".join([f"- {col}" for col in columns])
                    texts.append(column_text)
                
                summary_stats = analysis.get('summary_stats', {})
                if summary_stats:
                    stats_text = f"Ringkasan Statistik:\n{json.dumps(summary_stats, indent=2, ensure_ascii=False)}"
                    texts.append(stats_text)
            
            elif file_type == 'excel':
                sheets_data = file_data.get('data', {})
                
                for sheet_name, sheet_info in sheets_data.items():
                    data = sheet_info.get('data', [])
                    analysis = sheet_info.get('analysis', {})
                    
                    if data:
                        sample_data = data[:5]
                        sheet_text = f"Contoh Data Sheet '{sheet_name}':\n{json.dumps(sample_data, indent=2, ensure_ascii=False)}"
                        texts.append(sheet_text)
                    
                    if analysis:
                        analysis_text = f"Analisis Sheet '{sheet_name}':\n{json.dumps(analysis, indent=2, ensure_ascii=False)}"
                        texts.append(analysis_text)
            
            return texts
            
        except Exception as e:
            print(f"Error extracting texts: {e}")
            return [metadata_text] if 'metadata_text' in locals() else ["Data tidak dapat diproses dengan baik."]
    
    def is_available(self) -> bool:
        """Check if RAG service is available"""
        return hasattr(self, 'embedding_model') and hasattr(self, 'model')
    
    def get_chat_history(self, file_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a file"""
        return self.memories.get(file_id, [])
    
    def clear_chat_history(self, file_id: str) -> bool:
        """Clear chat history for a file"""
        if file_id in self.memories:
            self.memories[file_id] = []
            return True
        return False