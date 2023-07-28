import chromadb
import os

continue_option = input("This will reset the database in ./db. Are you sure you want to continue? (y/N) ")
if continue_option.lower() != "y":
    exit("Exiting.")

client = chromadb.PersistentClient("./db")

try:
    client.delete_collection("jb-c")
except ValueError:
    print("'jb-c' collection not found. Initializing as normal.")

collection = client.create_collection("jb-c")

# Files must be .txt files with newline-separated paragraphs.
# TODO: Metadata with source URL
documents, ids, metadatas = [], [], []
for root, dirs, files in os.walk("./documents"):
    for filename in files:
        if filename.endswith(".txt"):
            print(f"Adding {filename}")
            with open(os.path.join(root, filename), 'r') as file:
                data = file.read()
                paragraphs = data.split('\n\n')
                for i, paragraph in enumerate(paragraphs):
                    doc_id = filename + str(i)
                    ids.append(doc_id)
                    documents.append(paragraph)
                    metadatas.append({"type": os.path.basename(root)})

collection.add(documents=documents, metadatas=metadatas, ids=ids)
print(f"Database updated:\n{collection.peek()}")
