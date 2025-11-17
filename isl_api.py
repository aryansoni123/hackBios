# isl_api.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from isl_tokenizer import text_to_isl

app = FastAPI(title="English → ISL Token API (Stanford-enabled)")

# default path to vocab file (change if needed)
WORDS_FILE = os.environ.get("ISL_WORDS_FILE", "words.txt")

class ToIslRequest(BaseModel):
    text: str

class ToIslResponse(BaseModel):
    input: str
    tokens: List[str]
    filenames: List[str]
    missing_original_words: List[str]  # original words that needed character fallback
    meta: dict = {}

@app.post("/to_isl", response_model=ToIslResponse)
def to_isl(req: ToIslRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        tokens, filenames, meta = text_to_isl(text, WORDS_FILE)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # If something unexpected happens, return a helpful error
        raise HTTPException(status_code=500, detail=f"tokenization failed: {e}")

    # missing_original_words: tokens of length 1 and not present in words.txt (best-effort)
    missing = []
    try:
        valid_text = open(WORDS_FILE, 'r', encoding='utf-8').read().lower()
    except Exception:
        valid_text = ""
    for t in tokens:
        if len(t) == 1 and t.lower() not in valid_text:
            missing.append(t)

    return ToIslResponse(
        input=text,
        tokens=tokens,
        filenames=filenames,
        missing_original_words=missing,
        meta=meta
    )

if __name__ == "__main__":
    # Start with: python isl_api.py  (this runs using uvicorn below)
    import uvicorn
    uvicorn.run("isl_api:app", host="0.0.0.0", port=8000, reload=True)
