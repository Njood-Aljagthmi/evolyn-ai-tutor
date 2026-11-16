import os
import pickle
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Calculate the dynamic absolute path for data folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "../../data/knowledge_base"))

all_chunks = []

# 2. Smart loop through folders (languages and levels)
for language in ["python", "java"]:
    lang_dir = os.path.join(BASE_DIR, language)
    if not os.path.exists(lang_dir):
        continue
        
    for level in ["beginner", "intermediate", "advanced"]:  
        level_dir = os.path.join(lang_dir, level)
        if not os.path.exists(level_dir):
            continue
            
        print(f"📂 Checking directory: {language} -> {level}")
        
        # Search for files inside each level
        for file_name in os.listdir(level_dir):
            file_path = os.path.join(level_dir, file_name)
            
            # Read PDF files
            if file_name.endswith(".pdf"):
                print(f"📄 Loading and splitting PDF file: {file_name} ...")
                loader = PyPDFLoader(file_path)
                docs = loader.load()
            # Read Markdown files
            elif file_name.endswith(".md"):
                print(f"📄 Loading and splitting MD file: {file_name} ...")
                loader = UnstructuredMarkdownLoader(file_path)
                docs = loader.load()
            else:
                continue
                
            # Add detailed Metadata to each chunk for future retrieval context
            for doc in docs:
                doc.metadata["language"] = language
                doc.metadata["level"] = level
                doc.metadata["source_file"] = file_name

            # 3. Setup the text splitter configuration (Chunking)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=150,
                length_function=len
            )
            
            # Split the current document and add to global list
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)
            print(f"✅ Successfully chunked {file_name} into {len(chunks)} pieces.")

print(f"\n📊 Data Ingestion Completed! Total chunks generated: {len(all_chunks)}")

# 4. Save processed chunks locally for the next team member (Member 2)
if len(all_chunks) > 0:
    print("⏳ Saving chunks into a local file for Member 2 ...")
    
    # Define the output path in the main data folder
    output_file = os.path.normpath(os.path.join(CURRENT_DIR, "../../data/processed_chunks.pkl"))
    
    with open(output_file, "wb") as f:
        pickle.dump(all_chunks, f)
        
    print(f"🎉 Success! All chunks have been saved to: data/processed_chunks.pkl")
    print("Your task for 'Knowledge Base Prep' is officially finished. You can now push your work!")
else:
    print("❌ Warning: No files found. Please check your folder names and file structure in the hard drive.")

#FOR RUN 
#uv run --with langchain --with langchain-community --with langchain-openai --with chromadb --with pypdf --with unstructured --with markdown python ingest.py