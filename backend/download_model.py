from sentence_transformers import SentenceTransformer
import sys

def download_model():
    try:
        print("Downloading model...")
        model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        print("Model downloaded successfully")
        return True
    except Exception as e:
        print(f"Error downloading model: {str(e)}")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1) 