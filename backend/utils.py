# backend/utils.py
import pandas as pd
import os
import json

def merge_annotations(new_df: pd.DataFrame, annot_file: str, compiled_file: str):
    # Save or append to per-user file
    if os.path.exists(annot_file):
        old_df = pd.read_parquet(annot_file)
        combined = pd.concat([old_df, new_df]).drop_duplicates(subset=["segment_index", "annotator_id"])
    else:
        combined = new_df
    combined.to_parquet(annot_file, index=False)

    # Merge into compiled file (keeping all annotators)
    if os.path.exists(compiled_file):
        master_df = pd.read_parquet(compiled_file)
        master_combined = pd.concat([master_df, new_df]).drop_duplicates(subset=["segment_index", "annotator_id"])
    else:
        master_combined = new_df
    master_combined.to_parquet(compiled_file, index=False)

def load_registry(registry_path: str):
    if not os.path.exists(registry_path):
        return {"signals": []}
    with open(registry_path, "r") as f:
        return json.load(f)


def is_valid_annotator(annotator_id: str) -> bool:
    with open("annotators.json") as f:
        allowed = json.load(f)["annotators"]
    return annotator_id in allowed
