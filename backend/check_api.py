import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY tidak ditemukan di file .env")
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Coba cek koneksi API")

        # Jika tidak ada error, dan response berhasil
        if response.text:
            print("✅ API Gemini berhasil terhubung!")
            print(f"Respon: {response.text}")
        else:
            print("⚠️ API terhubung, tapi tidak ada respon teks. Mungkin ada masalah dengan konten yang dihasilkan.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat mencoba terhubung ke API Gemini.")
        print(f"Detail Error: {e}")