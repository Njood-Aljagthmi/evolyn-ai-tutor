import os
import pickle

# 1. Calculate the dynamic absolute path to the processed chunks file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_FILE = os.path.normpath(os.path.join(CURRENT_DIR, "../../data/processed_chunks.pkl"))

# 2. Check if the file exists before opening
if not os.path.exists(CHUNKS_FILE):
    print(f"❌ Error: Could not find the file at {CHUNKS_FILE}")
    print("Please make sure you ran ingest.py successfully first.")
    exit()

print(f"⏳ Loading chunks from: data/processed_chunks.pkl ...")

# 3. Open and load the binary pickle file
with open(CHUNKS_FILE, "rb") as f:
    chunks = pickle.load(f)

print(f"📊 Total number of chunks found in file: {len(chunks)}")

# 4. Inspect a few samples (e.g., the first 3 chunks)
print("\n🔍 --- Inspecting Sample Chunks ---")
samples_to_show = min(3, len(chunks)) # Show up to 3 samples

for i in range(samples_to_show):
    chunk = chunks[i]
    print(f"\n============= CHUNK #{i+1} =============")
    print(f"📋 METADATA: {chunk.metadata}")
    print(f"📝 CONTENT SAMPLE (First 200 characters):\n")
    # printing only the first 200 characters so your terminal doesn't overflow
    print(chunk.page_content[:200] + "...") 
    print("=======================================")

print("\n✅ Inspection complete!")

#uv run --with langchain python inspect_chunks.py