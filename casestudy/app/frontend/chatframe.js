const AGENT_API_BASE = window.__CASE_AGENT_BASE || "http://127.0.0.1:9000";
const STORAGE_PREFIX = "case-session:";

const chatHistory = document.getElementById("chat-history");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const clearBtn = document.getElementById("clear-history");
const quickChips = document.querySelectorAll("[data-quick]");
const aiReplyTitle = document.getElementById("ai-reply-title");
const aiReplyText = document.getElementById("ai-reply-text");
const sceneTitle = document.getElementById("scene-title");
const sceneBody = document.getElementById("scene-body");
const successTitle = document.getElementById("success-title");
const successList = document.getElementById("success-list");
const successEmpty = document.getElementById("success-empty");

const params = new URLSearchParams(window.location.search);
const sessionState = {
  caseId: params.get("case_id"),
  sessionId: params.get("session_id"),
  state: null,
};

const storageKey = (sessionId) => `${STORAGE_PREFIX}${sessionId}`;

const scrollChat = () => {
  if (!chatHistory) return;
  chatHistory.scrollTo({ top: chatHistory.scrollHeight, behavior: "smooth" });
};

const determineRole = (speaker) => {
  const normalized = (speaker || "").toLowerCase();
  if (!normalized) return "ai";
  if (
    normalized.includes("user") ||
    normalized.includes("người học") ||
    normalized.includes("learner") ||
    normalized.includes("bạn")
  ) {
    return "user";
  }
  return "ai";
};

const normalizeSpeaker = (speaker, fallbackRole) => {
  if (!speaker) return fallbackRole === "user" ? "Bạn" : "AI";
  return speaker;
};

const appendMessage = (text, role = "ai", speakerLabel) => {
  if (!chatHistory || !text) return;

  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "message--user" : "message--ai"}`;

  const avatar = document.createElement("div");
  avatar.className = "message__avatar";
  avatar.textContent = role === "user" ? "Bạn" : "AI";
  article.appendChild(avatar);

  const body = document.createElement("div");
  body.className = "message__body";

  const bubble = document.createElement("div");
  bubble.className = "message__bubble";
  if (role === "user") {
    bubble.classList.add("message__bubble--user");
  }

  if (speakerLabel && speakerLabel !== (role === "user" ? "Bạn" : "AI")) {
    const speakerEl = document.createElement("span");
    speakerEl.className = "message__speaker";
    speakerEl.textContent = speakerLabel;
    bubble.appendChild(speakerEl);
  }

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.appendChild(paragraph);

  body.appendChild(bubble);
  article.appendChild(body);
  chatHistory.appendChild(article);
  scrollChat();
};

const persistSession = (payload) => {
  if (!payload || !payload.session_id) return;
  try {
    sessionStorage.setItem(
      storageKey(payload.session_id),
      JSON.stringify({
        session_id: payload.session_id,
        case_id: payload.case_id,
        state: payload.state,
        saved_at: Date.now(),
      })
    );
  } catch (error) {
    console.warn("Không thể lưu session vào sessionStorage:", error);
  }
};

const loadStoredSession = (sessionId) => {
  if (!sessionId) return null;
  try {
    const raw = sessionStorage.getItem(storageKey(sessionId));
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn("Không thể đọc session từ sessionStorage:", error);
    return null;
  }
};

const updateUrlWithSession = () => {
  if (!sessionState.caseId || !sessionState.sessionId) return;
  const nextParams = new URLSearchParams();
  nextParams.set("case_id", sessionState.caseId);
  nextParams.set("session_id", sessionState.sessionId);
  window.history.replaceState({}, "", `${window.location.pathname}?${nextParams.toString()}`);
};

const createSession = async (caseId, userAction = "Bắt đầu nhiệm vụ.") => {
  const response = await fetch(`${AGENT_API_BASE}/api/agent/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      case_id: caseId,
      user_action: userAction,
    }),
  });
  if (!response.ok) {
    throw new Error(`Không thể tạo session (status ${response.status}).`);
  }
  return response.json();
};

const sendTurn = async (sessionId, userInput) => {
  const response = await fetch(`${AGENT_API_BASE}/api/agent/sessions/${sessionId}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput }),
  });
  if (!response.ok) {
    throw new Error(`Không thể gửi lượt mới (status ${response.status}).`);
  }
  return response.json();
};

const updateSummaryPanels = (state) => {
  if (aiReplyTitle) {
    aiReplyTitle.textContent = state?.current_event
      ? `AI • ${state.current_event}`
      : "AI Facilitator";
  }
  if (aiReplyText) {
    const text = (state?.ai_reply || "").trim();
    aiReplyText.textContent = text || "Chưa có phản hồi. Gửi câu hỏi để bắt đầu trao đổi.";
  }

  if (successTitle) {
    successTitle.textContent = state?.current_event
      ? `Success criteria • ${state.current_event}`
      : "Success criteria";
  }
  if (sceneTitle) {
    sceneTitle.textContent = state?.current_event
      ? `Hiện trường • ${state.current_event}`
      : "Hiện trường";
  }
  if (sceneBody) {
    const summary = (state?.scene_summary || "").trim();
    sceneBody.textContent = summary || "Chưa có tóm tắt hiện trường.";
  }

  if (!successList || !successEmpty) return;

  successList.innerHTML = "";

  const currentEvent = state?.current_event;
  const remainingKey = currentEvent ? `${currentEvent}_remaining_success_criteria` : null;
  const remaining =
    remainingKey && Array.isArray(state?.event_summary?.[remainingKey])
      ? state.event_summary[remainingKey]
      : [];

  const pickDescription = (item) => {
    if (!item) return "";
    if (typeof item === "string") {
      return item;
    }
    if (typeof item === "object") {
      return (
        item.description ||
        item.criterion ||
        item.title ||
        (Array.isArray(item.levels)
          ? item.levels.find((level) => level && level.descriptor)?.descriptor || ""
          : "")
      ).trim();
    }
    return "";
  };

  const readableRemaining = remaining
    .map((item) => pickDescription(item))
    .filter((text) => text.length);

  if (readableRemaining.length) {
    successEmpty.classList.add("hidden");
    successList.classList.remove("hidden");
    readableRemaining.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      successList.appendChild(li);
    });
  } else {
    successList.classList.add("hidden");
    successEmpty.classList.remove("hidden");
    successEmpty.textContent = "Hoàn thành toàn bộ tiêu chí cho event hiện tại.";
  }
};

const renderState = (state) => {
  if (!chatHistory) return;
  chatHistory.innerHTML = "";

  const history = Array.isArray(state?.dialogue_history) ? state.dialogue_history : [];
  if (!history.length && !state?.ai_reply) {
    appendMessage("Chưa có dữ liệu hội thoại. Hãy gửi thông điệp đầu tiên.", "ai");
    updateSummaryPanels(state);
    return;
  }

  history.forEach((entry) => {
    const content = entry?.content || entry?.text || entry?.message || "";
    if (!content) return;
    const speaker = entry?.speaker || entry?.persona || entry?.role || "";
    const role = determineRole(speaker);
    appendMessage(content, role, normalizeSpeaker(speaker, role));
  });
  if (state?.system_notice) {
    appendMessage(state.system_notice, "ai", "System");
  }

  updateSummaryPanels(state);
  scrollChat();
};

const bootstrapSession = async () => {
  let sessionPayload = null;

  if (sessionState.sessionId) {
    sessionPayload = loadStoredSession(sessionState.sessionId);
  }

  if (!sessionPayload && sessionState.caseId) {
    try {
      appendMessage("Đang khởi tạo session...", "ai");
      sessionPayload = await createSession(sessionState.caseId);
    } catch (error) {
      console.error(error);
      chatHistory.innerHTML = "";
      updateSummaryPanels(null);
      appendMessage("Không thể khởi tạo session. Vui lòng kiểm tra lại agent service.", "ai");
      return;
    }
  }

  if (!sessionPayload) {
    chatHistory.innerHTML = "";
    updateSummaryPanels(null);
    appendMessage("Chưa chọn case nào. Vui lòng quay lại danh sách case để bắt đầu.", "ai");
    return;
  }

  sessionState.sessionId = sessionPayload.session_id;
  sessionState.caseId = sessionPayload.case_id || sessionState.caseId;
  sessionState.state = sessionPayload.state;
  persistSession(sessionPayload);
  updateUrlWithSession();
  renderState(sessionPayload.state);
};

chatForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = chatInput?.value?.trim();
  if (!value) return;

  if (!sessionState.caseId) {
    appendMessage("Chưa có case nào được lựa chọn. Vui lòng quay lại danh sách case.", "ai");
    return;
  }

  appendMessage(value, "user");
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    if (!sessionState.sessionId) {
      const sessionPayload = await createSession(sessionState.caseId, value);
      sessionState.sessionId = sessionPayload.session_id;
      sessionState.caseId = sessionPayload.case_id || sessionState.caseId;
      sessionState.state = sessionPayload.state;
      persistSession(sessionPayload);
      updateUrlWithSession();
    } else {
      const turn = await sendTurn(sessionState.sessionId, value);
      sessionState.caseId = turn.case_id || sessionState.caseId;
      sessionState.state = turn.state;
      persistSession(turn);
    }
    renderState(sessionState.state);
  } catch (error) {
    console.error(error);
    appendMessage("Không thể gửi tin nhắn. Vui lòng thử lại sau.", "ai");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

chatInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    chatForm?.requestSubmit();
  }
});

clearBtn?.addEventListener("click", async () => {
  if (!sessionState.caseId) {
    chatHistory.innerHTML = "";
    updateSummaryPanels(null);
    appendMessage("Chưa có case nào được lựa chọn.", "ai");
    return;
  }
  chatHistory.innerHTML = "";
  appendMessage("Đang làm mới session...", "ai");
  try {
    const sessionPayload = await createSession(sessionState.caseId, "Bắt đầu nhiệm vụ.");
    sessionState.sessionId = sessionPayload.session_id;
    sessionState.caseId = sessionPayload.case_id || sessionState.caseId;
    sessionState.state = sessionPayload.state;
    persistSession(sessionPayload);
    updateUrlWithSession();
    renderState(sessionPayload.state);
  } catch (error) {
    console.error(error);
    chatHistory.innerHTML = "";
    updateSummaryPanels(null);
    appendMessage("Không thể làm mới session. Thử lại sau.", "ai");
  }
});

document.addEventListener("DOMContentLoaded", bootstrapSession);
