# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
import json
from utils import merge_annotations, load_registry, is_valid_annotator

app = FastAPI()

SIGNAL_DIR = "signals"
ANNOTATION_DIR = "annotations"
COMPILED_DIR = "compiled"
REGISTRY_FILE = "signal_registry.json"

os.makedirs(SIGNAL_DIR, exist_ok=True)
os.makedirs(ANNOTATION_DIR, exist_ok=True)
os.makedirs(COMPILED_DIR, exist_ok=True)

class AnnotationUpload(BaseModel):
    annotator_id: str
    signal_id: str
    annotations: list  # List of dicts

@app.get("/signals")
def list_signals():
    try:
        return load_registry(REGISTRY_FILE)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load_signal/{signal_id}/{annotator_id}")
def load_signal(signal_id: str, annotator_id: str):
    if not is_valid_annotator(annotator_id):
        raise HTTPException(status_code=403, detail="Invalid annotator ID")

    file_path = os.path.join(SIGNAL_DIR, f"{signal_id}.parquet")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Signal not found")
    df = pd.read_parquet(file_path)
    return JSONResponse(content=df.to_dict(orient="records"))

@app.post("/upload_annotations")
def upload_annotations(payload: AnnotationUpload):
    try:
        annot_file = os.path.join(ANNOTATION_DIR, f"{payload.annotator_id}_{payload.signal_id}.parquet")
        compiled_file = os.path.join(COMPILED_DIR, f"{payload.signal_id}_merged.parquet")
        
        new_df = pd.DataFrame(payload.annotations)
        merge_annotations(new_df, annot_file, compiled_file)

        return {"status": "success", "annotator": payload.annotator_id, "signal": payload.signal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/get_annotations/{annotator_id}/{signal_id}")
def get_annotations(annotator_id: str, signal_id: str):
    if not is_valid_annotator(annotator_id):
        raise HTTPException(status_code=403, detail="Invalid annotator ID")
        
    file_path = os.path.join("annotations", f"{annotator_id}_{signal_id}.parquet")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Annotation file not found")
    df = pd.read_parquet(file_path)
    return JSONResponse(content=df.to_dict(orient="records"))

@app.get("/validate_annotator/{annotator_id}")
def validate_annotator(annotator_id: str):
    if not is_valid_annotator(annotator_id):
        raise HTTPException(status_code=403, detail="Invalid annotator ID")
    return {"status": "ok"}
