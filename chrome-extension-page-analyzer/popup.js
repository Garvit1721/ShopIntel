document.addEventListener("DOMContentLoaded", () => {
  console.log("[Popup] DOM fully loaded");

  const analyzeBtn = document.getElementById("analyze");
  const tryOnBtn = document.getElementById("try-on-btn");
  const output = document.getElementById("output");
  const loading = document.getElementById("loading");
  const startChatBtn = document.getElementById("start-chat");
  const chatBox = document.getElementById("chatbox");
  const chatInput = document.getElementById("chat-input");
  const chatHistory = document.getElementById("chat-history");
  const sendChatBtn = document.getElementById("send-chat");

  let currentURL = "";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs && tabs.length > 0) {
      currentURL = tabs[0].url;
      console.log("[Popup] Current active tab URL:", currentURL);
    } else {
      console.warn("[Popup] No active tab found");
    }
  });

  chrome.storage.local.get("cachedMarkdown", (data) => {
    if (data.cachedMarkdown) {
      console.log("[Popup] Using cached markdown");
      output.innerHTML = marked.parse(data.cachedMarkdown);
    }
  });

  // Try-on button click handler
  tryOnBtn.addEventListener("click", () => {
    console.log("[Popup] Try-on button clicked");
    chrome.tabs.create({ url: "https://7134d43c0c09.ngrok-free.app/try-on" });
  });

  analyzeBtn.addEventListener("click", async () => {
    console.log("[Popup] Analyze button clicked");
    output.innerHTML = "";
    loading.innerHTML = '<div class="loading-spinner"></div>Analyzing page...';
    analyzeBtn.disabled = true;

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      console.log("[Popup] Sending request to /analyze-url for:", tab.url);

      const response = await fetch("http://127.0.0.1:4000/analyze-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url })
      });

      const result = await response.json();
      console.log("[Popup] Received response from server:", result);
      loading.innerHTML = "";
      analyzeBtn.disabled = false;

      if (result.markdown) {
        const markdown = result.markdown;
        output.innerHTML = marked.parse(markdown);
        chrome.storage.local.set({ cachedMarkdown: markdown });
        startChatBtn.style.display = "block";
        console.log("[Popup] Markdown displayed and cached.");
      } else {
        output.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        console.warn("[Popup] Error from server:", result.error);
      }
    } catch (err) {
      loading.innerHTML = "";
      analyzeBtn.disabled = false;
      output.innerHTML = `<div class="error">Failed to connect to server</div>`;
      console.error("[Popup] Fetch to /analyze-url failed:", err);
    }
  });

  startChatBtn.addEventListener("click", () => {
    console.log("[Popup] Chat button clicked, showing chat box.");
    chatBox.style.display = "block";
    chatInput.focus();
  });

  const sendMessage = async () => {
    const question = chatInput.value.trim();
    if (!question) {
      console.warn("[Popup] No question entered.");
      return;
    }

    console.log("[Popup] Sending chat question:", question);
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-message user-message';
    userDiv.textContent = question;
    chatHistory.appendChild(userDiv);
    
    chatInput.value = "";
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message assistant-message';
    loadingDiv.innerHTML = '<div class="loading-spinner"></div>Thinking...';
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
      const response = await fetch("http://127.0.0.1:4000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: currentURL, question })
      });

      const data = await response.json();
      console.log("[Popup] Chat response received:", data);
      
      // Remove loading indicator
      chatHistory.removeChild(loadingDiv);
      
      // Add assistant response as rendered markdown
      const assistantDiv = document.createElement('div');
      assistantDiv.className = 'chat-message assistant-message';
      assistantDiv.innerHTML = marked.parse(data.answer || "No response");
      chatHistory.appendChild(assistantDiv);
      
      chatHistory.scrollTop = chatHistory.scrollHeight;
    } catch (err) {
      console.error("[Popup] Fetch to /chat failed:", err);
      
      // Remove loading indicator
      chatHistory.removeChild(loadingDiv);
      
      // Add error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'chat-message assistant-message error';
      errorDiv.textContent = "Error fetching response";
      chatHistory.appendChild(errorDiv);
    }
  };

  sendChatBtn.addEventListener("click", sendMessage);
  
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});