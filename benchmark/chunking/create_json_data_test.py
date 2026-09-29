import pandas as pd
import json

# ==========================
# Config
# ==========================
EXCEL_PATH = r"D:\legal-technology-agentic-rag\data\data_test\data_test.xlsx"
OUTPUT_JSON = r"D:\legal-technology-agentic-rag\data\data_test\data_test.json"

# ==========================
# Read Excel
# ==========================
df = pd.read_excel(EXCEL_PATH)

dataset = []

for _, row in df.iterrows():

    # Evidence: tách theo xuống dòng
    # Evidence: chỉ tách khi gặp đúng chuỗi "\n"
    evidence = []
    if pd.notna(row["Evidence"]):
        evidence = [
            item.strip()
            for item in str(row["Evidence"]).split(r"\n")
            if item.strip()
        ]

    # Document: tách theo dấu ,
    documents = []
    if pd.notna(row["Document"]):
        documents = [
            item.strip()
            for item in str(row["Document"]).split(",")
            if item.strip()
        ]

    sample = {
        "id": str(row["ID"]).strip(),
        "category": str(row["Category"]).strip(),
        "question": str(row["Question"]).strip(),
        "ground_truth": str(row["Ground Truth Answer"]).strip(),
        "evidence": evidence,
        "documents": documents
    }

    dataset.append(sample)

# ==========================
# Save JSON
# ==========================
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print(f"Saved {len(dataset)} samples to {OUTPUT_JSON}")