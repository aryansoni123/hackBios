(function () {
  if (window.__islDummyInjected) return;
  window.__islDummyInjected = true;

  // --- UI SETUP ---
  const button = document.createElement("button");
  button.innerText = "ISL";
  Object.assign(button.style, {
    position: "fixed", bottom: "20px", right: "20px", zIndex: "999999",
    padding: "10px 14px", borderRadius: "999px", border: "none",
    fontWeight: "bold", cursor: "pointer", background: "#2563eb", color: "#fff",
    boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.3)"
  });
  document.body.appendChild(button);

  const panel = document.createElement("div");
  Object.assign(panel.style, {
    position: "fixed", top: "60px", right: "20px", width: "320px", height: "auto",
    padding: "15px", background: "#111827", color: "#e5e7eb", borderRadius: "10px",
    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.5)", display: "none", flexDirection: "column",
    gap: "10px", fontFamily: "Arial, sans-serif", zIndex: "999999", border: "1px solid #374151"
  });
  document.body.appendChild(panel);

  panel.innerHTML = `
      <div style="font-weight:bold; font-size:16px; text-align:center;">ISL Assistant</div>
      <div id="isl-status" style="font-size:12px; color:#9ca3af; text-align:center;">Ready</div>
      
      <div style="background:#000; width:100%; aspect-ratio:16/9; display:flex; align-items:center; justify-content:center; border-radius:8px; overflow:hidden; border:1px solid #374151;">
         <video id="isl-video-player" style="width:100%; height:100%; object-fit:cover;" playsinline></video>
      </div>

      <div style="display:flex; gap:10px;">
        <button id="isl-start" style="flex:1; padding:10px; background:#22c55e; border:none; borderRadius:6px; color:white; font-weight:bold; cursor:pointer;">Start</button>
        <button id="isl-stop" style="flex:1; padding:10px; background:#ef4444; border:none; borderRadius:6px; color:white; font-weight:bold; cursor:pointer; display:none;">Stop</button>
      </div>
      <div style="font-size:10px; color:#6b7280; text-align:center; margin-top:5px;">*Select "This Tab" & Enable Audio in Popup</div>
  `;

  const startBtn = panel.querySelector("#isl-start");
  const stopBtn = panel.querySelector("#isl-stop");
  const statusLabel = panel.querySelector("#isl-status");
  const videoPlayer = panel.querySelector("#isl-video-player");

  let mediaRecorder = null;
  let videoQueue = [];
  let isPlaying = false;
  let stream = null;

  button.onclick = () => panel.style.display = panel.style.display === "none" ? "flex" : "none";

  // --- MAIN CAPTURE LOGIC ---

  startBtn.onclick = async () => {
    try {
      // 1. Ask for Screen Share
      stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true // User MUST check "Share Tab Audio"
      });

      // 2. Check if user actually provided audio
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        alert("⚠️ NO AUDIO! You must check the 'Share Tab Audio' box in the popup.");
        // Stop the video stream immediately since it's useless without audio
        stream.getTracks().forEach(t => t.stop());
        return;
      }

      // --- CRITICAL FIX START ---
      // Create a new stream that contains ONLY the audio track.
      // This prevents the "Video vs Audio-only MIME type" crash.
      const audioStream = new MediaStream([audioTracks[0]]);
      // --- CRITICAL FIX END ---

      // 3. Create Recorder with the AUDIO-ONLY stream
      const mimeType = 'audio/webm;codecs=opus';
      // Check support just in case, fallback to default if needed
      const options = MediaRecorder.isTypeSupported(mimeType) ? { mimeType } : {};
      
      mediaRecorder = new MediaRecorder(audioStream, options);

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          const buffer = await event.data.arrayBuffer();
          const dataArray = Array.from(new Uint8Array(buffer));

          chrome.runtime.sendMessage({
            action: "processAudio",
            audioData: dataArray
          });
        }
      };

      // 4. Start recording
      mediaRecorder.start(1000);

      // UI Updates
      startBtn.style.display = "none";
      stopBtn.style.display = "block";
      updateStatus("Listening...", "#34d399");

      // Cleanup if user clicks "Stop Sharing" in browser UI
      stream.getVideoTracks()[0].onended = stopAll;

    } catch (err) {
      console.error("Capture Error:", err);
      alert("Error: " + err.message);
      updateStatus("Error", "#f87171");
    }
  };

  stopBtn.onclick = stopAll;

  function stopAll() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    if (stream) stream.getTracks().forEach(t => t.stop());
    
    startBtn.style.display = "block";
    stopBtn.style.display = "none";
    updateStatus("Stopped", "#9ca3af");
    videoQueue = [];
  }

  // --- QUEUE LOGIC ---
  function queueVideo(url) {
    videoQueue.push(url);
    if (!isPlaying) playNextVideo();
  }

  function playNextVideo() {
    if (videoQueue.length === 0) {
      isPlaying = false;
      updateStatus("Waiting...", "#fbbf24");
      return;
    }
    isPlaying = true;
    updateStatus("Signing...", "#34d399");
    videoPlayer.src = videoQueue.shift();
    videoPlayer.play().catch(e => console.log(e));
    videoPlayer.onended = playNextVideo;
  }

  function updateStatus(text, color) {
    statusLabel.innerText = text;
    statusLabel.style.color = color;
  }
})();