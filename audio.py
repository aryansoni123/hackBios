import pyaudio
import wave as wf
import os
from faster_whisper import WhisperModel

def record_chunk(p, stream, file_path, chunk_length=1):
    frames = []
    for _ in range(0, int(16000 / 1024 * chunk_length)):
        data = stream.read(1024)
        frames.append(data)
    wf_file = wf.open(file_path, 'wb')
    wf_file.setnchannels(1)
    wf_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf_file.setframerate(16000)
    wf_file.writeframes(b''.join(frames))
    wf_file.close()

def transcribe_chunk(model, file_path):
    segments, info = model.transcribe(file_path, beam_size=1)
    return " ".join([seg.text.strip() for seg in segments])

def main():
    # model_size must be a string (not a tuple). Default to CPU to avoid CUDA DLL issues.
    model_size = "medium.en"
    device = "cuda"  # change to "cuda" if your GPU and CUDA runtimes match
    # compute_type used only for GPU; keep None for CPU
    compute_type = None
    
    if device == "cpu":
        model = WhisperModel(model_size, device="cpu")
        print("Using CPU for transcription.")
    else:
        # set a valid compute_type for GPU when needed, e.g. "int8", "float16", or "int8_float16"
        
        compute_type = compute_type or "int8"
        model = WhisperModel(model_size, device="cuda", compute_type=compute_type)
        print(f"Using GPU for transcription with compute_type={compute_type}.")

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    accumulated_transcription = ""
    try:
        while True:
            chunk_file = "temp_chunk.wav"
            record_chunk(p, stream, chunk_file)
            transcription = transcribe_chunk(model, chunk_file)
            print(transcription)
            accumulated_transcription += (transcription + " ")
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
    except KeyboardInterrupt:
        print("Stopping...")
        with open("log.txt", "w", encoding="utf-8") as log_file:
            log_file.write(accumulated_transcription.strip())
    finally:
        print("LOG:", accumulated_transcription.strip())
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
