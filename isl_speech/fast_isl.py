from faster_whisper import WhisperModel
import spacy
import torch
import speech_recognition as sr
import os
import cv2
import threading
import queue
import json

# --- CONFIGURATION ---
VIDEO_FOLDER = r"D:\path\to\your\animations"  # CHANGE THIS
MODEL_SIZE = "medium.en"  # Options: "small.en", "medium.en", "large-v3"
COMPUTE_TYPE = "float16" if torch.cuda.is_available() else "int8"

# --- SYNONYM MAP (Critical for ISL Accuracy) ---
# Maps complex English words to simple files you actually have.
SYNONYMS = {
    "AUTOMOBILE": "CAR",
    "VEHICLE": "CAR",
    "RESIDENCE": "HOME",
    "HOUSE": "HOME",
    "PURCHASE": "BUY",
    "OBTAIN": "GET",
    "GREETINGS": "HELLO",
    # Add more here based on your video library!
}

# Shared Queue
animation_queue = queue.Queue()

def load_models():
    print(f"🚀 Loading Faster-Whisper ({MODEL_SIZE}) on GPU...")
    
    # Run on GPU with FP16 (Blazing fast)
    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE)
    
    print("📚 Loading NLP...")
    nlp = spacy.load("en_core_web_sm")
    
    print("✅ Systems Optimized & Ready.")
    return model, nlp

def english_to_isl_gloss(text, nlp):
    doc = nlp(text)
    
    # Buckets for SOV ordering
    time_words = []
    subject = []
    obj = []
    verb = []
    negative = []
    question = []
    adjectives = []
    
    for token in doc:
        # 1. Lemmatize & Upper: "Running" -> "RUN"
        word = token.lemma_.upper()
        
        # 2. Synonym Check: "AUTOMOBILE" -> "CAR"
        if word in SYNONYMS:
            word = SYNONYMS[word]

        # 3. Stop Word Filtering
        if token.is_stop and token.tag_ not in ["WDT", "WP", "WRB"] and token.dep_ != "neg":
            continue
            
        # 4. Grammar Bucketing
        dep = token.dep_
        pos = token.pos_
        
        if dep == "neg": 
            negative.append("NOT") # Force standard "NOT"
        elif token.tag_ in ["WDT", "WP", "WRB"]:
            question.append(word)
        elif "subj" in dep:
            subject.append(word)
        elif "obj" in dep:
            obj.append(word)
        elif pos == "VERB":
            verb.append(word)
        elif pos == "ADJ":
            adjectives.append(word)
        elif "time" in token.ent_type_ or pos == "ADV":
            time_words.append(word)
        else:
            obj.append(word)

    # ISL Structure: Time -> Subject -> Object -> Verb -> Negation -> Question
    isl_sequence = time_words + subject + obj + verb + negative + question
    return isl_sequence

def listener_thread(model, nlp):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 800 # Lower = more sensitive
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Listening (Optimized)...")
        
        while True:
            try:
                # Wait for voice
                audio_data = recognizer.listen(source, timeout=None)
                print("⚡ Processing...")

                # Write temp file
                with open("temp_fast.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())

                # --- FASTER-WHISPER INFERENCE ---
                # This is where the magic happens. It returns segments.
                segments, info = model.transcribe("temp_fast.wav", beam_size=5)
                
                # Combine segments into one string
                text = " ".join([segment.text for segment in segments]).strip()
                
                if text:
                    print(f"📝 Heard: {text}")
                    isl_gloss = english_to_isl_gloss(text, nlp)
                    print(f"🤟 ISL: {isl_gloss}")
                    
                    for word in isl_gloss:
                        animation_queue.put(word)
                        
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    # 1. Init Models
    if not torch.cuda.is_available():
        print("⚠️ WARNING: GPU not found. This will be slow on CPU.")
    
    model, nlp = load_models()

    # 2. Start Listener
    threading.Thread(target=listener_thread, args=(model, nlp), daemon=True).start()

    # 3. Video Player (Main Thread)
    print("🎬 Display Active.")
    while True:
        if not animation_queue.empty():
            word = animation_queue.get()
            video_path = os.path.join(VIDEO_FOLDER, f"{word}.mp4")
            
            if os.path.exists(video_path):
                cap = cv2.VideoCapture(video_path)
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    cv2.imshow('ISL Avatar', frame)
                    if cv2.waitKey(25) & 0xFF == ord('q'): return
                cap.release()
            else:
                # If word missing, try spelling it out? (Optional feature)
                print(f"⚠️ Asset missing: {word}.mp4")
        else:
            cv2.waitKey(50)

if __name__ == "__main__":
    main()