import os
from pathlib import Path
import json

# Define the docs directory path
docs_dir = Path(__file__).parent / "docs"

# Create a list of source documents from the docs directory
source_docs = [
    str(docs_dir / filename) 
    for filename in os.listdir(docs_dir) 
    if filename.endswith('.pdf')
]

#source_docs = [
#    "docs/EVS_EN_62304-2006+A1-2015_en.pdf",
#    ]

# Print the list of source documents
print(f"Found {len(source_docs)} PDF documents:")
for doc in source_docs:
    print(f"  - {Path(doc).name}")


from docling.document_converter import DocumentConverter

# Instantiate the doc converter
doc_converter = DocumentConverter()

# Directly pass list of files or streams to `convert_all`
conv_results_iter = doc_converter.convert_all(source_docs)  # previously `convert`

# Iterate over the generator to get a list of Docling documents
docs = [result.document for result in conv_results_iter]

# Save the conversion results to a file
output_file = "converted_documents.json"
with open(output_file, "w") as f:
    # Use export_to_dict() or model_dump() instead of to_json()
    json.dump([doc.export_to_dict() for doc in docs], f, indent=2)

print(f"\nConverted documents saved to {output_file}")
