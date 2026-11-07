// CommunityConnect AI - API layer.
//
// Agreed backend contract (proposed; to be confirmed by Developer 2):
//   POST /api/chat
//   Request:  { message, category, location }
//             category: "veterans" | "food" | "employment" | null
//   Response: { reply, resources: [{ name, category, description, location, phone, website }] }
//             phone / website may be null.
//
// MODES
//   "demo" - no network calls; returns clearly labeled fictional examples.
//   "live" - sends requests to the Flask backend. If the request fails, an
//            error is raised; live mode NEVER falls back to demo data.
//
// Switch modes by changing DEFAULT_MODE below, or per page load with a URL
// parameter: index.html?mode=live  or  index.html?mode=demo
//
// No credentials belong in this file. Snowflake authentication stays in Flask.

"use strict";

(function () {
  const DEFAULT_MODE = "live";

  // Ports used by static dev servers (python -m http.server, VS Code Live Server).
  // When the page is served from one of these, or opened as a file, requests go
  // to the local Flask server. Otherwise (e.g. Flask serves the frontend itself)
  // relative, same-origin URLs are used.
  const STATIC_DEV_PORTS = ["8000", "5500"];
  const LOCAL_FLASK_URL = "http://127.0.0.1:5050";

  const REQUEST_TIMEOUT_MS = 30000;
  const DEMO_DELAY_MS = 900;
  const MAX_RESOURCES = 20;

  const VALID_CATEGORIES = ["veterans", "food", "employment"];

  function resolveApiBase() {
    const { protocol, port } = window.location;
    if (protocol === "file:" || STATIC_DEV_PORTS.includes(port)) {
      return LOCAL_FLASK_URL;
    }
    return "";
  }

  function resolveMode() {
    const param = new URLSearchParams(window.location.search).get("mode");
    return param === "live" || param === "demo" ? param : DEFAULT_MODE;
  }

  const API_BASE = resolveApiBase();
  const CHAT_ENDPOINT = `${API_BASE}/api/chat`;
  const MODE = resolveMode();

  // Error with a `kind` the UI can turn into a friendly message:
  // "network" | "timeout" | "http" | "invalid_response"
  class ApiError extends Error {
    constructor(kind, message, status) {
      super(message);
      this.name = "ApiError";
      this.kind = kind;
      this.status = status ?? null;
    }
  }

  function buildPayload(message, category, location) {
    return {
      message,
      category: VALID_CATEGORIES.includes(category) ? category : null,
      location,
    };
  }

  // ---------- Response validation ----------

  function optionalString(value) {
    if (typeof value === "string") {
      const trimmed = value.trim();
      return trimmed === "" ? null : trimmed;
    }
    if (typeof value === "number") return String(value);
    return null;
  }

  function normalizeResource(raw) {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;

    const resource = {
      name: optionalString(raw.name),
      category: optionalString(raw.category)?.toLowerCase() ?? null,
      description: optionalString(raw.description),
      location: optionalString(raw.location),
      phone: optionalString(raw.phone),
      website: optionalString(raw.website),
    };

    // Skip entries with nothing meaningful to show.
    return resource.name || resource.description ? resource : null;
  }

  function normalizeResponse(data) {
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      throw new ApiError("invalid_response", "Response body is not a JSON object");
    }

    const reply = optionalString(data.reply);
    const rawResources = data.resources ?? [];
    if (!Array.isArray(rawResources)) {
      throw new ApiError("invalid_response", "`resources` must be an array");
    }
    if (reply === null && rawResources.length === 0) {
      throw new ApiError("invalid_response", "Response has no `reply` and no `resources`");
    }

    const resources = rawResources.map(normalizeResource).filter(Boolean).slice(0, MAX_RESOURCES);
    return { reply, resources, demo: false };
  }

  // ---------- Live mode ----------

  async function sendLive(payload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    let response;
    try {
      response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
    } catch (error) {
      if (error.name === "AbortError") {
        throw new ApiError("timeout", "Request timed out");
      }
      throw new ApiError("network", error.message || "Network request failed");
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      throw new ApiError("http", `Server responded with status ${response.status}`, response.status);
    }

    let data;
    try {
      data = await response.json();
    } catch {
      throw new ApiError("invalid_response", "Response body is not valid JSON");
    }
    return normalizeResponse(data);
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
    ApiError,
  };
})();
