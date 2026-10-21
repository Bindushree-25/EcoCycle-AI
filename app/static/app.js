(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const STORAGE_KEY = "ecocycle.scanHistory.v1";
  const form = $("#uploadForm");
  const input = $("#imageInput");
  const dropZone = $("#dropZone");
  const preview = $("#imagePreview");
  const fileMeta = $("#fileMeta");
  const fileName = $("#fileName");
  const analyzeButton = $("#analyzeButton");
  const statusLine = $("#statusLine");
  const resultEmpty = $("#resultEmpty");
  const resultContent = $("#resultContent");
  const toast = $("#toast");
  let selectedFile = null;
  let latestResult = null;
  let toastTimeout = null;

  function notify(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.remove("show"), 2800);
  }
  function setStatus(message, error = false) {
    statusLine.textContent = message;
    statusLine.classList.toggle("error", error);
  }
  function readHistory() {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      return Array.isArray(value) ? value.filter(item => item && item.id && item.prediction) : [];
    } catch (_) { return []; }
  }
  function saveHistory(items) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 100)));
      return true;
    } catch (_) {
      notify("Browser storage is unavailable. Export your report to keep a copy.");
      return false;
    }
  }
  function safeText(value) { return String(value ?? ""); }
  function prettyDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "Unknown date" : date.toLocaleString(undefined, {dateStyle:"medium", timeStyle:"short"});
  }
  function cleanLabel(value) {
    return safeText(value).replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
  }
  function resetFile() {
    selectedFile = null;
    input.value = "";
    preview.removeAttribute("src");
    preview.hidden = true;
    dropZone.classList.remove("preview-mode");
    fileMeta.hidden = true;
    fileName.textContent = "";
    setStatus("");
  }
  function setFile(file) {
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      resetFile(); setStatus("Use a JPG, PNG, or WebP image.", true); return;
    }
    if (file.size > 8 * 1024 * 1024) {
      resetFile(); setStatus("That image is larger than 8 MB. Choose a smaller file.", true); return;
    }
    if (file.size === 0) {
      resetFile(); setStatus("This file is empty. Choose another image.", true); return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = () => {
      preview.src = reader.result;
      preview.hidden = false;
      dropZone.classList.add("preview-mode");
    };
    reader.onerror = () => setStatus("The image preview could not be loaded. Try another file.", true);
    reader.readAsDataURL(file);
    fileName.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    fileMeta.hidden = false;
    setStatus("Image ready. Select Analyze image to continue.");
  }
  input.addEventListener("change", () => setFile(input.files[0]));
  $("#removeFile").addEventListener("click", resetFile);
  ["dragenter", "dragover"].forEach(type => dropZone.addEventListener(type, e => {
    e.preventDefault(); dropZone.classList.add("dragging");
  }));
  ["dragleave", "drop"].forEach(type => dropZone.addEventListener(type, e => {
    e.preventDefault(); dropZone.classList.remove("dragging");
  }));
  dropZone.addEventListener("drop", e => setFile(e.dataTransfer?.files?.[0]));

  function guidanceMarkup(guidance) {
    const steps = (guidance.steps || []).map(step => `<li>${escapeHtml(step)}</li>`).join("");
    return `<div class="guidance-box"><h4>Recommended next steps</h4><p>${escapeHtml(guidance.summary || "Check local handling guidance before disposal.")}</p><ul>${steps}</ul><p class="guidance-caution"><strong>Safety note:</strong> ${escapeHtml(guidance.caution || "Do not dismantle electronic equipment based on an image classification.")}</p></div>`;
  }
  function escapeHtml(value) {
    return safeText(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }
  function renderResult(data, {save = true, imageData = null} = {}) {
    latestResult = {...data, imageData};
    resultEmpty.hidden = true;
    resultContent.hidden = false;
    const confidence = Math.max(0, Math.min(1, Number(data.confidence) || 0));
    const top = Array.isArray(data.top_k) ? data.top_k : [];
    const topMarkup = top.map(item => {
      const percent = Math.max(0, Math.min(100, (Number(item.confidence) || 0) * 100));
      return `<div class="top-prediction"><span>${escapeHtml(cleanLabel(item.label))}</span><div class="mini-track"><i style="width:${percent}%"></i></div><b>${percent.toFixed(1)}%</b></div>`;
    }).join("");
    const caution = data.low_confidence ? `<div class="safety-note"><span>!</span><p>Confidence is below the app's 55% review threshold. Treat this prediction as uncertain and verify the item manually.</p></div>` : "";
    resultContent.innerHTML = `
      <div class="eyebrow">CLASSIFICATION COMPLETE</div>
      <h3 class="prediction-title">${escapeHtml(cleanLabel(data.prediction))}</h3>
      <p class="prediction-subtitle">Predicted category · ${escapeHtml(data.filename || selectedFile?.name || "Saved scan")}</p>
      <div class="confidence-row"><span>Model confidence</span><strong>${(confidence * 100).toFixed(1)}%</strong></div>
      <div class="confidence-track" role="img" aria-label="Model confidence ${(confidence * 100).toFixed(1)} percent"><div class="confidence-fill" style="width:${confidence * 100}%"></div></div>
      ${topMarkup ? `<div class="top-predictions"><h4>Other likely categories</h4>${topMarkup}</div>` : ""}
      ${caution}
      ${guidanceMarkup(data.guidance || {})}
      <div class="result-actions"><button type="button" id="exportReport">Export report ↓</button><button type="button" id="showDecision">Compare next steps ↗</button></div>`;
    $("#exportReport").addEventListener("click", () => exportReport(latestResult));
    $("#showDecision").addEventListener("click", () => openModal("decisionModal"));
    if (save) {
      const history = readHistory();
      history.unshift({
        id: (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`),
        prediction: data.prediction,
        confidence,
        timestamp: new Date().toISOString(),
        guidance: data.guidance || {},
        top_k: top,
        filename: data.filename || selectedFile?.name || "scan"
      });
      saveHistory(history);
      renderHistory();
    }
  }
  function showModelUnavailable(message) {
    resultEmpty.hidden = false;
    resultContent.hidden = true;
    setStatus(message, true);
  }
  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (!selectedFile) { setStatus("Choose an image before analyzing.", true); return; }
    const originalLabel = analyzeButton.innerHTML;
    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing image…";
    setStatus("Validating image and contacting the local inference service…");
    const body = new FormData();
    body.append("image", selectedFile, selectedFile.name);
    try {
      const response = await fetch("/api/predict", {method:"POST", body});
      let data;
      try { data = await response.json(); } catch (_) { throw new Error("The server returned an unreadable response."); }
      if (!response.ok || !data.success) {
        const error = new Error(data.error || `Analysis failed (${response.status}).`);
        error.code = data.code; error.status = response.status; throw error;
      }
      renderResult(data);
      setStatus("Analysis complete. Review the safety guidance before acting.");
      $("#resultPanel").scrollIntoView({behavior:"smooth", block:"nearest"});
    } catch (error) {
      const message = error.code === "model_unavailable"
        ? "The public AI model could not be loaded. Check your internet connection and restart the scan; no fake prediction was generated."
        : error.status === 0 || error instanceof TypeError
          ? "Could not reach the local service. Start the Flask server and try again."
          : error.message || "Analysis failed. Please try another image.";
      setStatus(message, true);
      resultEmpty.hidden = false;
      resultContent.hidden = true;
      notify(message);
    } finally {
      analyzeButton.disabled = false;
      analyzeButton.innerHTML = originalLabel;
    }
  });

  function exportReport(item) {
    if (!item) { notify("There is no scan to export yet."); return; }
    const report = {
      application: "EcoCycle AI — Flagship Studio Release",
      generated_at: new Date().toISOString(),
      classification: {
        predicted_category: item.prediction,
        confidence: Number(item.confidence),
        top_predictions: item.top_k || [],
        timestamp: item.timestamp || new Date().toISOString()
      },
      recommendations: item.guidance || {},
      limitations: [
        "The model prediction is not a safety inspection or a guarantee of item identity.",
        "Confidence is the model's output score, not a calibrated probability unless separately validated.",
        "Verify local acceptance rules and service details before taking action."
      ]
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `ecocycle-scan-${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    notify("Scan report exported.");
  }
  function renderHistory() {
    const history = readHistory();
    $("#scanCount").textContent = String(history.length);
    const counts = {};
    history.forEach(item => { counts[item.prediction] = (counts[item.prediction] || 0) + 1; });
    const top = Object.entries(counts).sort((a,b) => b[1]-a[1])[0];
    $("#topCategory").textContent = top ? cleanLabel(top[0]) : "—";
    const body = $("#historyBody");
    if (!history.length) {
      body.innerHTML = '<tr><td colspan="5" class="history-empty">Your successful scans will appear here. No sample activity is shown.</td></tr>';
      return;
    }
    body.innerHTML = history.slice(0, 20).map(item => {
      const next = item.guidance?.route ? cleanLabel(item.guidance.route) : "Review guidance";
      return `<tr><td>${escapeHtml(cleanLabel(item.prediction))}</td><td>${escapeHtml(prettyDate(item.timestamp))}</td><td>${(Math.max(0,Math.min(1,Number(item.confidence)||0))*100).toFixed(1)}%</td><td>${escapeHtml(next)}</td><td><button type="button" class="inline-action history-export" data-id="${escapeHtml(item.id)}">Export ↓</button></td></tr>`;
    }).join("");
    $$(".history-export").forEach(button => button.addEventListener("click", () => {
      const item = readHistory().find(row => row.id === button.dataset.id);
      if (item) exportReport(item);
    }));
  }
  $("#clearHistory").addEventListener("click", () => {
    if (!readHistory().length) { notify("There is no saved history to clear."); return; }
    if (window.confirm("Clear all EcoCycle scan history saved in this browser? This cannot be undone.")) {
      localStorage.removeItem(STORAGE_KEY); renderHistory(); notify("Browser history cleared.");
    }
  });

  const modalIds = ["decisionModal", "impactModal", "finderModal"];
  function openModal(id) {
    const dialog = document.getElementById(id);
    if (dialog && typeof dialog.showModal === "function") dialog.showModal();
  }
  $$("[data-open]").forEach(button => button.addEventListener("click", () => openModal(button.dataset.open)));
  $("#decideButton").addEventListener("click", () => {
    const works = $("#works").value;
    const damaged = $("#damaged").value;
    const dataDevice = $("#dataDevice").value;
    const reuseReady = $("#reuseReady").value;
    let title, advice, steps;
    if (damaged === "yes") {
      title = "Prioritize safe specialist handling.";
      advice = "Do not charge, open, or dismantle the item. If a battery is hot, swollen, leaking, hissing, or smoking, move away and seek appropriate local emergency or hazardous-waste advice.";
      steps = ["Keep the item away from heat and combustible materials if it is safe to do so.", "Contact an e-waste service and explain the damage before transporting it.", "Do not ship or place it in a normal collection bin without confirming acceptance."];
    } else if (works === "yes" && reuseReady === "yes") {
      title = "Consider reuse before recycling.";
      advice = "A working item may retain value through donation, resale, or continued use.";
      steps = ["Check whether anyone can use it as-is.", "If it stores data, back up and securely erase it before transfer.", "If resale or donation is unsuitable, check repair or authorized e-waste collection options."];
    } else if (works === "no" && reuseReady === "yes") {
      title = "Check whether repair is worthwhile.";
      advice = "Repair can extend useful life, but the cost, safety, and availability of parts matter.";
      steps = ["Ask a qualified repair provider for an assessment.", "Compare repair cost with replacement and warranty options.", "If repair is not practical, use a suitable electronics collection route."];
    } else {
      title = "Find a suitable collection route.";
      advice = "Use a service that explicitly accepts your item type and condition.";
      steps = ["Check manufacturer or retailer take-back programs.", "Search local e-waste collection services.", "Confirm acceptance, fees, and preparation instructions directly."];
    }
    if (dataDevice === "yes" || dataDevice === "unknown") steps.unshift("Before donating or reselling, identify any stored personal data and securely erase it where possible.");
    const result = $("#decisionResult");
    result.innerHTML = `<strong>${escapeHtml(title)}</strong><p>${escapeHtml(advice)}</p><ul>${steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul><p><b>Reminder:</b> This is general guidance, not an inspection or verified local referral.</p>`;
    result.hidden = false;
  });

  $("#impactCalculate").addEventListener("click", () => {
    const quantity = Number($("#impactQuantity").value);
    const overrideRaw = $("#impactWeight").value.trim();
    const override = overrideRaw === "" ? null : Number(overrideRaw);
    const categoryWeight = Number($("#impactType").value);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
      notify("Enter a whole number of items between 1 and 1,000."); return;
    }
    if (override !== null && (!Number.isFinite(override) || override <= 0 || override > 1000)) {
      notify("Enter a valid weight between 0.01 and 1,000 kg."); return;
    }
    const weight = override ?? categoryWeight;
    const total = weight * quantity;
    const result = $("#impactResult");
    result.innerHTML = `<span class="summary-label">ESTIMATED ELECTRONIC WASTE MASS</span><span class="big-number">${total.toLocaleString(undefined,{maximumFractionDigits:2})} kg</span><p>Based on ${quantity} item(s) at ${weight} kg each. This is a weight estimate only, not a carbon or pollution-savings claim.</p><p><b>What it means:</b> if this mass is collected through an appropriate reuse or recycling route, it may be diverted from general waste. Actual recovery depends on the item and the service.</p>`;
    result.hidden = false;
  });
  $("#findPlaces").addEventListener("click", () => {
    const location = $("#locationQuery").value.trim();
    const type = $("#locationType").value;
    if (!location) { notify("Enter a city, area, or postal code first."); $("#locationQuery").focus(); return; }
    const query = `${type} ${location}`;
    // Use Google Maps as the default provider: OpenStreetMap's public website may
    // temporarily rate-limit repeated search requests (HTTP 429). This is a hand-off,
    // not a claim that EcoCycle verifies the listed centres.
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    $("#finderNote").textContent = "Opening Google Maps search. Listings are third-party information; verify the address, acceptance policy, operating hours, and fees directly. If it does not open, try the OpenStreetMap alternative below.";
    window.open(url, "_blank", "noopener,noreferrer");
  });
  $("#findPlacesOsm")?.addEventListener("click", () => {
    const location = $("#locationQuery").value.trim();
    const type = $("#locationType").value;
    if (!location) { notify("Enter a city, area, or postal code first."); $("#locationQuery").focus(); return; }
    const query = `${type} ${location}`;
    const url = `https://www.openstreetmap.org/search?query=${encodeURIComponent(query)}`;
    $("#finderNote").textContent = "Opening OpenStreetMap. It may temporarily return a rate-limit error; if so, use Google Maps instead. Verify all third-party listings directly.";
    window.open(url, "_blank", "noopener,noreferrer");
  });
  $("#locationQuery").addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); $("#findPlaces").click(); }
  });
  $("#mobileMenu").addEventListener("click", () => {
    const nav = $(".main-nav");
    const isOpen = nav.classList.toggle("open");
    $("#mobileMenu").setAttribute("aria-expanded", String(isOpen));
  });
  $$(".main-nav a").forEach(link => link.addEventListener("click", () => {
    $(".main-nav").classList.remove("open");
    $("#mobileMenu").setAttribute("aria-expanded", "false");
  }));
  // A lightweight status check clarifies whether the app's server is available; it never invents model readiness.
  fetch("/api/health").then(r => r.json()).then(data => {
    if (!data.model_file_present) {
      $("#historyHint").textContent = "AI model downloads automatically on the first scan; internet is required for initial setup.";
    }
  }).catch(() => {
    setStatus("Local server status could not be checked. Start Flask before analyzing images.", true);
  });
  renderHistory();
})();
