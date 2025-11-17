import speech_recognition as sr
import whisper
import spacy
import torch
import warnings

# --- IMPORT YOUR ANIMATION MODEL HERE ---
# from animation_engine import generate_avatar_animation 
# (Uncomment the line above if you have the file)

# --- CONFIGURATION ---
MODEL_TYPE = "small" # Fast and Accurate on GPU

warnings.filterwarnings("ignore")

def load_models():
    print(f"⏳ Loading Whisper ({MODEL_TYPE}) on GPU...")
    model = whisper.load_model(MODEL_TYPE, device="cuda")
    nlp = spacy.load("en_core_web_sm")
    print("✅ Brain Ready!")
    return model, nlp

def text_to_isl(text, nlp):
    doc = nlp(text)
    isl_words = []
    for token in doc:
        word = token.lemma_.upper()
        if token.is_stop and token.tag_ not in ["WDT", "WP", "WRB"] and token.dep_ != "neg":
            continue
        isl_words.append(word)
    return isl_words

def main():
    if not torch.cuda.is_available():
        print("❌ GPU not found. Enabling CPU mode (Slower).")

    model, nlp = load_models()
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 1000
    recognizer.dynamic_energy_threshold = True
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("\n🎤 Conversation Started. Speak naturally...")
        
        while True:
            try:
                # 1. Listen
                audio = recognizer.listen(source, timeout=None)
                
                # 2. Transcribe
                with open("temp_live.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                
                result = model.transcribe("temp_live.wav", fp16=True)
                english_text = result["text"].strip()
                
                if english_text:
                    print(f"📝 English: {english_text}")
                    
                    # 3. Convert to ISL
                    isl_gloss_list = text_to_isl(english_text, nlp)
                    print(f"📤 Sending to Model: {isl_gloss_list}")
                    
                    # --- 4. TRIGGER YOUR OTHER MODEL HERE ---
                    # Example: 
                    # generate_avatar_animation(isl_gloss_list)
                    
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()