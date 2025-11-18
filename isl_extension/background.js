// background.js

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 1. HANDLE AUDIO PROCESSING
  if (request.action === "processAudio") {
    
    // Convert Array back to Blob
    const uint8Array = new Uint8Array(request.audioData);
    const blob = new Blob([uint8Array], { type: 'audio/webm;codecs=opus' });

    const formData = new FormData();
    formData.append("audio_chunk", blob, "chunk.webm");

    // Fetch to Localhost (Bypasses YouTube CORS)
    fetch("http://localhost:5000/process-audio", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ success: true, data: data });
    })
    .catch(error => {
      console.error("API Error:", error);
      sendResponse({ success: false, error: error.message });
    });

    return true; // Keep channel open for async response
  }
});