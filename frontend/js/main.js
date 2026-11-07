// CommunityConnect AI - UI logic (vanilla JS).
// API requests and demo/live mode live in api.js (window.CommunityConnectAPI).

"use strict";

const API = window.CommunityConnectAPI;
const DEFAULT_LOCATION = "Miami-Dade County";

const CATEGORIES = {
  veterans: "Veteran Support",
  food: "Food Assistance",
  employment: "Employment",
};

const STARTER_PROMPTS = {
  veterans: "I'm a veteran and I'd like to learn about support programs available to me.",
  food: "I'm looking for food assistance in Miami-Dade.",
  employment: "I'm looking for employment assistance and job resources.",
};

const state = {
  category: null,
  loading: false,
};

// ---------- DOM ----------

const els = {
  navToggle: document.querySelector(".nav-toggle"),
  nav: document.getElementById("site-nav"),
  categoryCards: document.querySelectorAll(".category-card"),
  selectedCategory: document.getElementById("selected-category"),
  clearCategory: document.getElementById("clear-category"),
  chatLog: document.getElementById("chat-log"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  sendBtn: document.getElementById("send-btn"),
  chips: document.querySelectorAll(".chip"),
  resourceList: document.getElementById("resource-list"),
  demoNotice: document.getElementById("demo-notice"),
  resourcesNotice: document.getElementById("resources-demo-notice"),
  modeBadge: document.getElementById("mode-badge"),
};

// ---------- Helpers ----------

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function hasValue(value) {
  return typeof value === "string" && value.trim() !== "";
}

// Only allow http(s) links to avoid javascript: or other unsafe URLs.
function safeUrl(value) {
  if (!hasValue(value)) return null;
  try {
    const url = new URL(value.trim());
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

function scrollChatToBottom() {
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

// ---------- Navigation ----------

function closeNav() {
  els.nav.classList.remove("open");
  els.navToggle.setAttribute("aria-expanded", "false");
}

els.navToggle.addEventListener("click", () => {
  const open = els.nav.classList.toggle("open");
  els.navToggle.setAttribute("aria-expanded", String(open));
});

els.nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeNav));

// ---------- Categories ----------

function setCategory(category) {
  state.category = CATEGORIES[category] ? category : null;

  els.categoryCards.forEach((card) => {
    card.setAttribute("aria-pressed", String(card.dataset.category === state.category));
  });

  els.selectedCategory.textContent = state.category ? CATEGORIES[state.category] : "All categories";
  els.clearCategory.hidden = !state.category;
}

els.categoryCards.forEach((card) => {
  card.addEventListener("click", () => {
    const category = card.dataset.category;
    setCategory(category);

    // Pre-fill a relevant starter message the user can edit or send.
    if (!els.chatInput.value.trim()) {
      els.chatInput.value = STARTER_PROMPTS[category];
      autoResize();
      updateSendState();
    }

    document.getElementById("chat").scrollIntoView({ behavior: "smooth" });
    els.chatInput.focus({ preventScroll: true });
  });
});

els.clearCategory.addEventListener("click", () => setCategory(null));

// ---------- Chat messages ----------

function addMessage(role, text, options = {}) {
  const isUser = role === "user";
  const wrapper = el("div", `message ${role}${options.demo ? " demo" : ""}`);
  const avatar = el("span", "message-avatar", isUser ? "You" : options.demo ? "Demo" : "AI");
  avatar.setAttribute("aria-hidden", "true");

  const bubble = el("div", "message-bubble", text);
  if (options.demo) {
    bubble.prepend(el("span", "demo-tag", "Demo example \u2013 not a real AI recommendation"));
  }
  const label = el("span", "sr-only", isUser ? "You said: " : "Assistant: ");
  bubble.prepend(label);

  wrapper.append(avatar, bubble);
  els.chatLog.append(wrapper);
  scrollChatToBottom();
  return wrapper;
}

function showTyping() {
  const wrapper = el("div", "message ai typing-row");
  const avatar = el("span", "message-avatar", "AI");
  avatar.setAttribute("aria-hidden", "true");
  const bubble = el("div", "message-bubble typing");
  bubble.setAttribute("role", "status");
  bubble.append(el("span"), el("span"), el("span"), el("span", "sr-only", "Assistant is typing"));
  wrapper.append(avatar, bubble);
  els.chatLog.append(wrapper);
  scrollChatToBottom();
  return wrapper;
}

// ---------- Resource cards ----------

function createResourceCard(resource, options = {}) {
  const card = el("article", `resource-card${options.demo ? " demo" : ""}`);

  if (options.demo) {
    card.append(el("span", "demo-tag", "Fictional example \u2013 not a real organization"));
  }

  const categoryKey = hasValue(resource.category) ? resource.category.trim().toLowerCase() : "";
  const categoryLabel = CATEGORIES[categoryKey] || (hasValue(resource.category) ? resource.category : "General");
  card.append(el("span", `badge ${CATEGORIES[categoryKey] ? categoryKey : ""}`.trim(), categoryLabel));

  card.append(el("h3", null, hasValue(resource.name) ? resource.name : "Unnamed organization"));

  card.append(
    hasValue(resource.description)
      ? el("p", "resource-desc", resource.description)
      : el("p", "resource-desc muted", "No description available.")
  );

  const meta = el("dl", "resource-meta");

  const addRow = (label, content) => {
    const row = el("div");
    const dd = el("dd");
    dd.append(content);
    row.append(el("dt", null, label), dd);
    meta.append(row);
  };

  addRow(
    "Location",
    hasValue(resource.location) ? document.createTextNode(resource.location) : el("span", "muted", "Not listed")
  );

  if (hasValue(resource.phone)) {
    const tel = resource.phone.replace(/[^\d+]/g, "");
    if (/\d{3,}/.test(tel)) {
      const link = el("a", null, resource.phone);
      link.href = `tel:${tel}`;
      addRow("Phone", link);
    } else {
      addRow("Phone", document.createTextNode(resource.phone));
    }
  } else {
    addRow("Phone", el("span", "muted", "Not available"));
  }

  const website = safeUrl(resource.website);
  if (website) {
    const link = el("a", null, "Visit website");
    link.href = website;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `Visit website for ${resource.name || "this organization"} (opens in new tab)`);
    addRow("Website", link);
  } else {
    addRow("Website", el("span", "muted", "Not available"));
  }

  card.append(meta);
  return card;
}

function renderResources(resources, options = {}) {
  els.resourceList.replaceChildren();
  els.resourcesNotice.hidden = !options.demo;

  if (!Array.isArray(resources) || resources.length === 0) {
    els.resourceList.append(
      el("p", "empty-state", "No matching resources were returned. Try rephrasing or choosing a different category.")
    );
    return;
  }

  resources.forEach((resource) => {
    if (resource && typeof resource === "object") {
      els.resourceList.append(createResourceCard(resource, options));
    }
  });
}

// ---------- Errors ----------

function friendlyError(error) {
  switch (error?.kind) {
    case "timeout":
      return "Sorry, that took too long. Please try again in a moment.";
    case "network":
      return "We couldn't reach the CommunityConnect assistant right now. The service may be offline or still starting up. Please try again shortly.";
    case "http":
      return error.status >= 500
        ? "The CommunityConnect assistant ran into a problem on our side. Please try again in a moment."
        : "Sorry, we couldn't process that request. Please try rephrasing your message.";
    case "invalid_response":
      return "We received an unexpected response from the assistant. Please try again.";
    default:
      return "Sorry, something went wrong while getting your answer. Please try again.";
  }
}

// ---------- Input handling ----------

function updateSendState() {
  els.sendBtn.disabled = state.loading || els.chatInput.value.trim() === "";
}

function setLoading(loading) {
  state.loading = loading;
  els.chatInput.disabled = loading;
  els.chips.forEach((chip) => (chip.disabled = loading));
  els.chatLog.setAttribute("aria-busy", String(loading));
  updateSendState();
}

function autoResize() {
  els.chatInput.style.height = "auto";
  els.chatInput.style.height = `${Math.min(els.chatInput.scrollHeight, 160)}px`;
}

async function handleSend(rawMessage) {
  const message = rawMessage.trim();
  if (!message || state.loading) return;

  addMessage("user", message);
  els.chatInput.value = "";
  autoResize();
  setLoading(true);
  const typing = showTyping();

  try {
    const data = await API.sendChat(message, state.category, DEFAULT_LOCATION);
    const demo = data?.demo === true;
    typing.remove();
    addMessage("ai", hasValue(data?.reply) ? data.reply : "Here are some resources that may help.", { demo });
    renderResources(data?.resources, { demo });
    if (Array.isArray(data?.resources) && data.resources.length > 0) {
      els.resourceList.closest("section").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    typing.remove();
    console.error("Chat request failed:", error);
    addMessage("ai error", friendlyError(error));
  } finally {
    setLoading(false);
    els.chatInput.focus({ preventScroll: true });
  }
}

els.chatInput.addEventListener("input", () => {
  autoResize();
  updateSendState();
});

els.chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    handleSend(els.chatInput.value);
  }
});

els.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  handleSend(els.chatInput.value);
});

els.chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    if (chip.dataset.category) setCategory(chip.dataset.category);
    handleSend(chip.dataset.prompt);
  });
});

// ---------- Init ----------

document.addEventListener("DOMContentLoaded", () => {
  els.demoNotice.hidden = !API.isDemo;
  els.modeBadge.textContent = API.isDemo ? "Demo mode" : "Live mode";
  els.modeBadge.classList.toggle("live", !API.isDemo);

  addMessage(
    "ai",
    "Hi there! I'm the CommunityConnect assistant. I can help you find veteran support, food assistance, and employment programs in Miami-Dade County.\n\nTell me what you need, choose a category, or try one of the example questions below."
  );
  updateSendState();
});

// Expose rendering helpers for testing and future integration.
window.CommunityConnect = { renderResources, createResourceCard, setCategory };
