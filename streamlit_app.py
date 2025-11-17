# streamlit_app.py
import streamlit as st
import os
import json
from isl_tokenizer import text_to_isl

st.set_page_config(page_title="ISL Tokenizer Demo", layout="centered")

st.title("ISL Tokenizer — Demo")
st.markdown("Convert English text → sequence of ISL tokens / sign filenames.\n\nYou can run the tokenizer locally (preferred) or send the text to a running `/to_isl` FastAPI server.")

# Config
WORDS_PATH = st.text_input("Path to words.txt", value=os.environ.get("ISL_WORDS_FILE", "words.txt"))
use_api = st.checkbox("Call remote REST API instead of local function", value=False)
api_url = st.text_input("If using REST API, enter base URL (e.g. http://127.0.0.1:8000)", value="http://127.0.0.1:8000")

text_input = st.text_area("Enter English text (from your speech->text model)", value="Are you ok", height=120)

col1, col2 = st.columns(2)
with col1:
    if st.button("Convert"):
        if not text_input.strip():
            st.warning("Enter some text first.")
        else:
            if use_api:
                # call REST API
                try:
                    import requests
                    resp = requests.post(f"{api_url.rstrip('/')}/to_isl", json={"text": text_input})
                    if resp.status_code != 200:
                        st.error(f"API returned {resp.status_code}: {resp.text}")
                    else:
                        data = resp.json()
                        st.success("Received response from API")
                        st.json(data)
                        st.download_button("Download JSON", json.dumps(data, indent=2), file_name="isl_result.json")
                except Exception as e:
                    st.error(f"Failed to call API: {e}")
            else:
                # call local function directly
                try:
                    tokens, filenames, meta = text_to_isl(text_input, WORDS_PATH)
                    out = {"input": text_input, "tokens": tokens, "filenames": filenames, "meta": meta}
                    st.success("Tokenization (local) completed")
                    st.json(out)
                    st.download_button("Download JSON", json.dumps(out, indent=2), file_name="isl_result.json")
                except FileNotFoundError as e:
                    st.error(f"words.txt not found: {e}")
                except Exception as e:
                    st.error(f"Tokenization failed: {e}")
with col2:
    st.info("Tips")
    st.write("- Make sure `words.txt` path is correct (one token per line).")
    st.write("- If you use the remote API option, ensure your FastAPI server has CORS enabled for Streamlit origin.")
    st.write("- For heavy parsing (Stanford parser) ensure Java is installed and stanford jars are present or downloaded.")
    st.write("- If you see long startup logs from stanza, those are model-loading messages — wait until finished.")

st.divider()
st.markdown("**Quick actions**")
st.write("You can run the FastAPI server via uvicorn and then use the `Call remote REST API` option above.")
