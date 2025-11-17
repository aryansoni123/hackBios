import whisper
import spacy
import sounddevice as sd
from scipy.io.wavfile import write
import os

# --- CONFIGURATION ---
SAMPLE_RATE = 44100  # Hertz
DURATION = 5         # How long to record (seconds)
OUTPUT_FILENAME = "user_input.wav"

# Load Models (Do this once at startup)
print("⏳ Loading models... (this may take a moment)")
whisper_model = whisper.load_model("base")
nlp = spacy.load("en_core_web_sm")
print("✅ Models loaded!")

def record_audio():
    """Captures audio from the microphone"""
    print(f"\n🎤 Recording for {DURATION} seconds... Speak now!")
    my_recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()  # Wait until recording is finished
    write(OUTPUT_FILENAME, SAMPLE_RATE, my_recording)
    print("✅ Recording saved.")
    return OUTPUT_FILENAME

def text_to_isl_gloss(text):
    """
    Converts English grammar to ISL Gloss (Keywords).
    Critical for matching your animation database.
    """
    doc = nlp(text)
    
    # Buckets for reordering
    time_words = []
    subject = []
    obj = []
    verb = []
    negative = [] # For "not", "never"
    question = [] # For "what", "where"
    adjectives = []
    
    for token in doc:
        # 1. LEMMATIZATION: Convert "running" -> "run", "cars" -> "car"
        # This is crucial to match your animation filenames!
        word = token.lemma_.upper()
        
        # 2. STOP WORDS: Skip "is", "am", "are", "the" (unless it's a question word)
        if token.is_stop and token.tag_ not in ["WDT", "WP", "WP$", "WRB"] and token.dep_ != "neg":
            continue
            
        # 3. CATEGORIZATION (Dependency Parsing)
        dep = token.dep_
        pos = token.pos_
        
        if dep == "neg":
            negative.append(word)
        elif token.tag_ in ["WDT", "WP", "WP$", "WRB"]: # Who, What, Where
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
            # If we can't categorize it easily, put it with object for now
            obj.append(word)

    # 4. REORDERING RULES (ISL: Time + Subject + Object + Verb + Negation + Question)
    # Note: We place adjectives before the nouns they modify in this simple version
    
    isl_sequence = time_words + subject + adjectives + obj + verb + negative + question
    
    return isl_sequence

# --- MAIN EXECUTION FLOW ---
if __name__ == "__main__":
    # Step 1: Record
    audio_file = record_audio()
    
    # Step 2: Audio -> English Text (Whisper)
    print("🧠 Transcribing...")
    result = whisper_model.transcribe(audio_file)
    english_text = result["text"].strip()
    print(f"📝 English: {english_text}")
    
    # Step 3: English Text -> ISL Keywords (NLP)
    isl_keywords = text_to_isl_gloss(english_text)
    
    print(f"🤟 ISL Sequence: {isl_keywords}")
    
    # Step 4: (Integration Point)
    # Here you would send 'isl_keywords' to your existing animation model
    # Example: 
    # play_animations(isl_keywords)