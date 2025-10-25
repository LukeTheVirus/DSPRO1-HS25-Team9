# save_model_locally.py
from sentence_transformers import SentenceTransformer

model_name = "BAAI/bge-large-en-v1.5"
# This will download and save the model to a new directory
# named 'BAAI/bge-large-en-v1.5' in the current folder.
SentenceTransformer(model_name).save(f'./{model_name}')

print(f"Model saved to ./{model_name}")