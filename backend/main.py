# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
import json
from utils import merge_annotations, load_registry, is_valid_annotator
from collections import defaultdict
import time
import threading
from contextlib import asynccontextmanager
from threading import Lock

buffer_lock = Lock()



SIGNAL_DIR = "signals"
ANNOTATION_DIR = "annotations"
COMPILED_DIR = "compiled"
REGISTRY_FILE = "signal_registry.json"

os.makedirs(SIGNAL_DIR, exist_ok=True)
os.makedirs(ANNOTATION_DIR, exist_ok=True)
os.makedirs(COMPILED_DIR, exist_ok=True)

annotation_buffer = defaultdict(list)  # Keyed by (annotator_id, signal_id)
SAVE_INTERVAL = 10  # write every 10 annotations

def background_saver():
    while True:
        time.sleep(SAVE_INTERVAL)
        with buffer_lock:
            for key, buffer in list(annotation_buffer.items()):
                if buffer:
                    annotator_id, signal_id = key
                    annot_file = os.path.join(ANNOTATION_DIR, f"{annotator_id}_{signal_id}.csv")
                    compiled_file = os.path.join(COMPILED_DIR, f"{signal_id}_merged.csv")
                    new_df = pd.DataFrame(buffer)
                    merge_annotations(new_df, annot_file, compiled_file)
                    annotation_buffer[key].clear()
                    print(f"Saved {len(new_df)} annotations for {key}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=background_saver, daemon=True).start()
    print("🟢 Background saver started.")
    yield
    # Optional: Add final cleanup here
    print("🔴 Server shutdown: lifespan ended.")

app = FastAPI(lifespan=lifespan)

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
        key = (payload.annotator_id, payload.signal_id)
        with buffer_lock:
            annotation_buffer[key].extend(payload.annotations)
            print(f"[Buffered] now has {len(annotation_buffer[key])} items")
        return {"status": "buffered", "buffer_length": len(annotation_buffer[key])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/flush_annotations")
def flush_annotations(payload: AnnotationUpload):
    try:
        key = (payload.annotator_id, payload.signal_id)
        buffer_data = annotation_buffer.pop(key, [])

        if not buffer_data:
            return {"status": "nothing to flush"}

        annot_file = os.path.join(ANNOTATION_DIR, f"{payload.annotator_id}_{payload.signal_id}.csv")
        compiled_file = os.path.join(COMPILED_DIR, f"{payload.signal_id}_merged.csv")
        new_df = pd.DataFrame(buffer_data)
        merge_annotations(new_df, annot_file, compiled_file)

        return {"status": "flushed", "count": len(buffer_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_annotations/{annotator_id}/{signal_id}")
def get_annotations(annotator_id: str, signal_id: str):
    if not is_valid_annotator(annotator_id):
        raise HTTPException(status_code=403, detail="Invalid annotator ID")
        
    file_path = os.path.join("annotations", f"{annotator_id}_{signal_id}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Annotation file not found")
    df = pd.read_csv(file_path)
    return JSONResponse(content=df.to_dict(orient="records"))

@app.get("/validate_annotator/{annotator_id}")
def validate_annotator(annotator_id: str):
    if not is_valid_annotator(annotator_id):
        raise HTTPException(status_code=403, detail="Invalid annotator ID")
    return {"status": "ok"}


