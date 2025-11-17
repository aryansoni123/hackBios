import speech_recognition as sr
import whisper
import spacy
import torch
import warnings

# Filter warnings
warnings.filterwarnings("ignore")

# Check for GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Hardware Detected: {DEVICE.upper()}")
if DEVICE == "cuda":
    print(f"   GPU Name: {torch.cuda.get_device_name(0)}")

print("⏳ Loading Whisper Model on GPU...")
# 'base' is fast, but on GPU you might even be able to use 'small' or 'medium' for better accuracy!
audio_model = whisper.load_model("base", device=DEVICE)
print("✅ Whisper Loaded!")

print("⏳ Loading NLP Model...")
nlp = spacy.load("en_core_web_sm")
print("✅ NLP Loaded!")

def text_to_isl_gloss(text):
    doc = nlp(text)
    
    # Buckets for reordering
    time_words = []
    subject = []
    obj = []
    verb = []
    negative = []
    question = []
    adjectives = []
    
    for token in doc:
        word = token.lemma_.upper()
        
        if token.is_stop and token.tag_ not in ["WDT", "WP", "WP$", "WRB"] and token.dep_ != "neg":
            continue
            
        dep = token.dep_
        pos = token.pos_
        
        if dep == "neg":
            negative.append(word)
        elif token.tag_ in ["WDT", "WP", "WP$", "WRB"]:
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

    isl_sequence = time_words + subject + adjectives + obj + verb + negative + question
    if not isl_sequence:
        isl_sequence = [t.lemma_.upper() for t in doc if not t.is_stop]
    return isl_sequence

def main():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 1000
    recognizer.dynamic_energy_threshold = True

    print("\n🎧 --- REAL-TIME ISL (GPU POWERED) ---")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while True:
            try:
                print("\n🎤 Listening...")
                audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                print("⚡ Processing on GPU...")
                
                # Save temp file
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio_data.get_wav_data())
                
                # Transcribe (FP16 is faster on GPU)
                result = audio_model.transcribe("temp_audio.wav", fp16=True)
                english_text = result["text"].strip()
                
                if english_text:
                    print(f"📝 English: {english_text}")
                    isl_gloss = text_to_isl_gloss(english_text)
                    print(f"👋 ISL Output: {isl_gloss}")
                    
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()