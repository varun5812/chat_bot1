const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const chatMessages = document.querySelector("#chatMessages");
const sourcesContainer = document.querySelector("#sources");
const sessionId = crypto.randomUUID();

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
  setLoading(true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }

    appendMessage("assistant", data.answer);
    renderSources(data.sources || []);
  } catch (error) {
    appendMessage("assistant error", error.message);
  } finally {
    setLoading(false);
    messageInput.focus();
  }
});

function appendMessage(role, text) {
  const message = document.createElement("article");
  message.className = `message ${role}`;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  message.appendChild(paragraph);

  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderSources(sources) {
  sourcesContainer.innerHTML = "";

  if (!sources.length) {
    sourcesContainer.innerHTML = '<p class="empty">No sources returned.</p>';
    return;
  }

  for (const source of sources) {
    const item = document.createElement("article");
    item.className = "source";

    const title = document.createElement("strong");
    title.textContent = formatSourceTitle(source);

    const snippet = document.createElement("p");
    snippet.textContent = source.snippet || "";

    item.append(title, snippet);
    sourcesContainer.appendChild(item);
  }
}

function formatSourceTitle(source) {
  const page = source.page !== null && source.page !== undefined ? `, page ${source.page + 1}` : "";
  return `${source.source || "Unknown source"}${page}`;
}

function setLoading(isLoading) {
  const button = chatForm.querySelector("button");
  button.disabled = isLoading;
  button.textContent = isLoading ? "Sending" : "Send";
}
