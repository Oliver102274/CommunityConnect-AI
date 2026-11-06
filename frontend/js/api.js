// CommunityConnect AI - API layer.
//
// Proposed backend contract (to be confirmed by Developer 2):
//   POST /api/chat
//   Request:  { message, category, location }
//             category: "veterans" | "food" | "employment" | null
//   Response: { reply, resources: [{ name, category, description, location, phone, website }] }
//
// MODES
//   "demo" - no network calls; returns clearly labeled fictional examples.
//   "live" - sends requests to the Flask backend.
//
// Switch modes by changing DEFAULT_MODE below, or per page load with a URL
// parameter: index.html?mode=live  or  index.html?mode=demo

"use strict";

(function () {
  const DEFAULT_MODE = "demo";

  // When the page is served by Flask (port 5000) use relative URLs; otherwise
  // (file:// or a static dev server) point at the local Flask server.
  const API_BASE = window.location.port === "5000" ? "" : "http://127.0.0.1:5000";
  const CHAT_ENDPOINT = `${API_BASE}/api/chat`;
  const REQUEST_TIMEOUT_MS = 30000;
  const DEMO_DELAY_MS = 900;

  const VALID_CATEGORIES = ["veterans", "food", "employment"];

  function resolveMode() {
    const param = new URLSearchParams(window.location.search).get("mode");
    return param === "live" || param === "demo" ? param : DEFAULT_MODE;
  }

  const MODE = resolveMode();

  function buildPayload(message, category, location) {
    return {
      message,
      category: VALID_CATEGORIES.includes(category) ? category : null,
      location,
    };
  }

  // ---------- Live mode ----------

  async function sendLive(payload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      const data = await response.json();
      return { ...data, demo: false };
    } finally {
      clearTimeout(timer);
    }
  }

  // ---------- Demo mode ----------
  // All organizations below are FICTIONAL placeholders. They intentionally
  // have no phone numbers, addresses, or websites.

  const DEMO_DATA = {
    veterans: {
      reply:
        "Here are some example veteran support programs to show how results will look. " +
        "Once connected to our resource database, this is where verified Miami-Dade programs will appear.",
      resources: [
        {
          name: "Example Veteran Benefits Navigation Program",
          category: "veterans",
          description:
            "Fictional example of a program that helps veterans understand and apply for benefits.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
        {
          name: "Example Veteran Transition Support Center",
          category: "veterans",
          description:
            "Fictional example of a center offering transition, housing navigation, and peer support.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
      ],
    },
    food: {
      reply:
        "Here are some example food assistance resources to show how results will look. " +
        "Real food pantries and meal programs will appear once the backend is connected.",
      resources: [
        {
          name: "Example Community Food Pantry",
          category: "food",
          description: "Fictional example of a pantry providing groceries to local residents.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
        {
          name: "Example Nutrition Benefits Help Desk",
          category: "food",
          description: "Fictional example of a service that helps people apply for nutrition benefits.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
      ],
    },
    employment: {
      reply:
        "Here are some example employment resources to show how results will look. " +
        "Verified workforce programs will appear once the backend is connected.",
      resources: [
        {
          name: "Example Career Readiness Workshop",
          category: "employment",
          description: "Fictional example of a program offering resume help and interview practice.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
        {
          name: "Example Job Training Program",
          category: "employment",
          description: "Fictional example of a skills training and job placement program.",
          location: "Miami-Dade County (example)",
          phone: null,
          website: null,
        },
      ],
    },
  };

  const KEYWORDS = {
    veterans: ["veteran", "military", "va ", "service member", "army", "navy", "marine", "air force", "coast guard"],
    food: ["food", "pantry", "meal", "hungry", "groceries", "snap", "nutrition", "eat"],
    employment: ["job", "employ", "work", "career", "resume", "hiring", "training", "interview"],
  };

  function detectCategories(message) {
    const text = ` ${message.toLowerCase()} `;
    return VALID_CATEGORIES.filter((key) => KEYWORDS[key].some((word) => text.includes(word)));
  }

  function sendDemo(payload) {
    const matched = payload.category ? [payload.category] : detectCategories(payload.message);

    let result;
    if (matched.length === 0) {
      result = {
        reply:
          "I can help with veteran support, food assistance, and employment in Miami-Dade County. " +
          "Could you tell me a bit more about what you need, or pick a category above?",
        resources: [],
      };
    } else {
      // A message like "veteran looking for a job" matches more than one category.
      result = {
        reply: matched.map((key) => DEMO_DATA[key].reply).join("\n\n"),
        resources: matched.flatMap((key) => DEMO_DATA[key].resources),
      };
    }

    return new Promise((resolve) =>
      setTimeout(() => resolve({ ...structuredClone(result), demo: true }), DEMO_DELAY_MS)
    );
  }

  // ---------- Public API ----------

  function sendChat(message, category, location) {
    const payload = buildPayload(message, category, location);
    return MODE === "live" ? sendLive(payload) : sendDemo(payload);
  }

  window.CommunityConnectAPI = {
    mode: MODE,
    isDemo: MODE === "demo",
    endpoint: CHAT_ENDPOINT,
    sendChat,
  };
})();
