(function () {
  if (window.__islDummyInjected) return;
  window.__islDummyInjected = true;

  // Floating button
  const button = document.createElement("button");
  button.innerText = "ISL";
  button.style.position = "fixed";
  button.style.bottom = "20px";
  button.style.right = "20px";
  button.style.zIndex = "999999";
  button.style.padding = "10px 14px";
  button.style.borderRadius = "999px";
  button.style.border = "none";
  button.style.fontWeight = "bold";
  button.style.cursor = "pointer";
  button.style.background = "#2563eb";
  button.style.color = "#fff";
  button.style.boxShadow = "0px 4px 12px rgba(0, 0, 0, 0.3)";
  document.body.appendChild(button);

  // Side panel
  const panel = document.createElement("div");
  panel.style.position = "fixed";
  panel.style.top = "60px";
  panel.style.right = "20px";
  panel.style.width = "300px";
  panel.style.height = "400px";
  panel.style.padding = "10px";
  panel.style.background = "#111827";
  panel.style.color = "#e5e7eb";
  panel.style.borderRadius = "10px";
  panel.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.5)";
  panel.style.display = "none";
  panel.style.flexDirection = "column";
  panel.style.gap = "8px";
  panel.style.fontFamily = "Arial, sans-serif";
  document.body.appendChild(panel);

  panel.innerHTML = `
      <div style="text-align:center;font-weight:bold;margin-bottom:6px;">ISL Assistant (Prototype)</div>
      <textarea id="isl-input" placeholder="Type or paste text here..." 
        style="width:100%;height:100px;padding:8px;background:#020617;color:#e5e7eb;border:1px solid #374151;border-radius:8px;resize:none;font-size:14px;"></textarea>
      <button id="isl-convert" style="padding:10px;margin-top:4px;background:#2563eb;border:none;border-radius:8px;color:white;font-weight:bold;cursor:pointer;">
        Convert to ISL
      </button>
      <div id="isl-output" style="margin-top:10px;display:flex;flex-direction:column;gap:6px;">
        <div style="font-size:13px;color:#9ca3af;">Sign output will appear here...</div>
      </div>
    `;

  const convertBtn = panel.querySelector("#isl-convert");
  const input = panel.querySelector("#isl-input");
  const output = panel.querySelector("#isl-output");

  button.addEventListener("click", () => {
    panel.style.display = panel.style.display === "none" ? "flex" : "none";
  });

  convertBtn.addEventListener("click", () => {
    const text = input.value.trim();
    if (!text) {
      output.innerHTML = `<div style="color:#f87171;">Please enter some text.</div>`;
      return;
    }

    // Dummy output: simulate ISL conversion
    output.innerHTML = `
      <div style="font-size:14px;">Showing signs for:</div>
      <div style="font-weight:bold;color:#34d399;">"${text}"</div>
      <div style="margin-top:10px;font-size:13px;">(Demo-only: This will show sign videos in future)</div>
    `;
  });
})();