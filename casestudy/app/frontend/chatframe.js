const AGENT_API_BASE = window.__CASE_AGENT_BASE || "http://127.0.0.1:9000";
const STORAGE_PREFIX = "case-session:";
const SESSION_OWNER_ENDPOINT = "/api/auth/session-owner";
const recordedSessions = new Set();

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
const sttToggle = document.getElementById("stt-toggle");
const ttsToggle = document.getElementById("tts-toggle");
const voiceStatus = document.getElementById("voice-status");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const hasSttSupport = typeof SpeechRecognition === "function";
const hasLocalTtsSupport = Boolean(window.speechSynthesis && window.SpeechSynthesisUtterance);
const canPlayAudioElement = typeof Audio === "function";
const hasAnyTtsSupport = hasLocalTtsSupport || canPlayAudioElement;

let recognitionInstance = null;
let sttListening = false;
let sttShouldContinue = false;
let ttsEnabled = false;

const params = new URLSearchParams(window.location.search);
const sessionState = {
  caseId: params.get("case_id"),
  sessionId: params.get("session_id"),
  state: null,
  ownerRecorded: false,
  lastServerTts: null,
};

let activeServerAudio = null;
let serverSegmentQueue = [];
let currentServerSegment = null;

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

const setButtonPressed = (button, pressed) => {
  if (!button) return;
  button.setAttribute("aria-pressed", pressed ? "true" : "false");
};

const updateSttButtonLabel = () => {
  if (!sttToggle) return;
  const label = sttShouldContinue || sttListening ? "Dung" : "Thu am";
  const span = sttToggle.querySelector("span");
  if (span) {
    span.textContent = label;
  }
};

const updateVoiceStatus = (message, tone = "neutral") => {
  if (!voiceStatus) return;
  voiceStatus.textContent = message;
  voiceStatus.dataset.tone = tone;
};

const refreshVoiceStatus = () => {
  if (!voiceStatus) return;
  if (!hasSttSupport && !hasAnyTtsSupport) {
    updateVoiceStatus("Trinh duyet chua ho tro giong.", "error");
    return;
  }
  if (sttListening) {
    updateVoiceStatus("Dang nghe... noi ro de nhan.", "active");
    return;
  }
  if (activeServerAudio) {
    const label = currentServerSegment || "AI";
    updateVoiceStatus(`Dang phat ${label}...`, "active");
    return;
  }
  if (ttsEnabled) {
    updateVoiceStatus("Se doc tu dong phan hoi AI.", "active");
    return;
  }
  updateVoiceStatus("Chuc nang giong san sang.");
};

const appendSpeechTextToInput = (spokenText) => {
  if (!chatInput || !spokenText) return;
  const incoming = spokenText.trim();
  if (!incoming) return;
  const existing = chatInput.value.trim();
  chatInput.value = existing ? `${existing} ${incoming}` : incoming;
  chatInput.dispatchEvent(new Event("input", { bubbles: true }));
  chatInput.focus();
};

const normalizeServerTts = (payload) => {
  if (!payload) return null;
  const segments = Array.isArray(payload.tts_segments)
    ? payload.tts_segments
        .map((segment) => ({
          speaker: segment?.speaker || "AI",
          personaId: segment?.persona_id || null,
          text: segment?.text || "",
          voice: segment?.voice || payload.tts_voice || "",
          audio: segment?.audio || null,
          mimeType: segment?.mime_type || payload.tts_mime_type || "audio/wav",
        }))
        .filter((segment) => segment.text || segment.audio)
    : [];
  const combinedSegmentText = segments
    .map((segment) => (segment.text ? `${segment.speaker}: ${segment.text}` : ""))
    .filter(Boolean)
    .join(" ");
  const text =
    payload.tts_text ||
    combinedSegmentText ||
    (payload.state && payload.state.ai_reply) ||
    payload.ai_reply ||
    "";
  const audio = payload.tts_audio || "";
  if (!text && !audio && !segments.length) {
    return null;
  }
  return {
    audio,
    mimeType: payload.tts_mime_type || "audio/wav",
    voice: payload.tts_voice || "",
    model: payload.tts_model || "",
    text,
    segments,
  };
};

const storeServerTts = (payload) => {
  sessionState.lastServerTts = normalizeServerTts(payload);
  return sessionState.lastServerTts;
};

const stopServerAudio = () => {
  if (activeServerAudio) {
    try {
      activeServerAudio.pause();
    } catch (error) {
      // ignore
    }
  }
  activeServerAudio = null;
  serverSegmentQueue = [];
  currentServerSegment = null;
  if (ttsEnabled) {
    refreshVoiceStatus();
  }
};

const playServerAudioSource = (segment) => {
  if (!segment || !segment.audio || !canPlayAudioElement) return false;
  const mime = segment.mimeType || "audio/wav";
  const source = `data:${mime};base64,${segment.audio}`;
  const label = segment.speaker || "AI";
  try {
    const audio = new Audio(source);
    activeServerAudio = audio;
    currentServerSegment = label;
    updateVoiceStatus(`Dang phat ${label}...`, "active");
    audio.addEventListener("ended", () => {
      if (activeServerAudio !== audio) {
        return;
      }
      activeServerAudio = null;
      if (serverSegmentQueue.length) {
        const next = serverSegmentQueue.shift();
        if (!playServerAudioSource(next)) {
          currentServerSegment = null;
          refreshVoiceStatus();
        }
      } else {
        currentServerSegment = null;
        refreshVoiceStatus();
      }
    });
    audio.addEventListener("error", (event) => {
      console.warn("Server TTS playback error:", event);
      if (activeServerAudio !== audio) {
        return;
      }
      activeServerAudio = null;
      if (serverSegmentQueue.length) {
        const next = serverSegmentQueue.shift();
        if (!playServerAudioSource(next)) {
          currentServerSegment = null;
          updateVoiceStatus("Khong phat duoc am thanh AI.", "error");
        }
      } else {
        currentServerSegment = null;
        updateVoiceStatus("Khong phat duoc am thanh AI.", "error");
      }
    });
    audio
      .play()
      .catch((error) => {
        console.warn("Cannot autoplay server TTS:", error);
        if (activeServerAudio === audio) {
          activeServerAudio = null;
        }
        if (serverSegmentQueue.length) {
          const next = serverSegmentQueue.shift();
          if (!playServerAudioSource(next)) {
            currentServerSegment = null;
            refreshVoiceStatus();
          }
        } else {
          currentServerSegment = null;
          refreshVoiceStatus();
        }
      });
    return true;
  } catch (error) {
    console.warn("Cannot play server TTS:", error);
    return false;
  }
};

const playServerSegments = (segments) => {
  if (!ttsEnabled || !canPlayAudioElement) return false;
  const playable = (segments || []).filter((segment) => segment && segment.audio);
  if (!playable.length) return false;
  stopServerAudio();
  serverSegmentQueue = playable.slice(1);
  return playServerAudioSource(playable[0]);
};

const playLatestServerAudio = () => {
  if (!sessionState.lastServerTts || !ttsEnabled) return false;
  const segments = sessionState.lastServerTts.segments || [];
  if (Array.isArray(segments) && segments.length) {
    if (playServerSegments(segments)) {
      return true;
    }
  }
  if (sessionState.lastServerTts.audio) {
    return playServerSegments([
      {
        audio: sessionState.lastServerTts.audio,
        mimeType: sessionState.lastServerTts.mimeType,
        speaker: "AI",
        text: sessionState.lastServerTts.text || "",
      },
    ]);
  }
  return false;
};

const ensureRecognition = () => {
  if (!hasSttSupport) return null;
  if (recognitionInstance) return recognitionInstance;
  const instance = new SpeechRecognition();
  instance.lang = "vi-VN";
  instance.interimResults = true;
  instance.maxAlternatives = 1;
  instance.continuous = true;

  instance.addEventListener("start", () => {
    sttListening = true;
    setButtonPressed(sttToggle, true);
    refreshVoiceStatus();
    updateSttButtonLabel();
  });

  instance.addEventListener("end", () => {
    sttListening = false;
    setButtonPressed(sttToggle, false);
    if (sttShouldContinue) {
      setTimeout(() => {
        try {
          instance.start();
        } catch (error) {
          console.warn("Speech recognition restart failed:", error);
          sttShouldContinue = false;
          refreshVoiceStatus();
        }
      }, 300);
    } else {
      refreshVoiceStatus();
    }
    updateSttButtonLabel();
  });

  instance.addEventListener("result", (event) => {
    let finalTranscript = "";
    let interimTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      if (result.isFinal) {
        finalTranscript += result[0].transcript;
      } else {
        interimTranscript += result[0].transcript;
      }
    }
    if (interimTranscript) {
      updateVoiceStatus(`Dang nghe: ${interimTranscript.trim()}`, "active");
    }
    if (finalTranscript) {
      appendSpeechTextToInput(finalTranscript);
      refreshVoiceStatus();
    }
  });

  instance.addEventListener("error", (event) => {
    console.warn("Speech recognition error:", event.error || event.message);
    updateVoiceStatus("Khong the thu am. Kiem tra micro.", "error");
    sttShouldContinue = false;
    sttListening = false;
    setButtonPressed(sttToggle, false);
    updateSttButtonLabel();
  });

  recognitionInstance = instance;
  return recognitionInstance;
};

const toggleSpeechRecognition = () => {
  if (!hasSttSupport) {
    updateVoiceStatus("Trinh duyet khong ho tro nhan giong.", "error");
    return;
  }
  const instance = ensureRecognition();
  if (!instance) return;
  try {
    if (sttShouldContinue || sttListening) {
      sttShouldContinue = false;
      updateSttButtonLabel();
      instance.stop();
      return;
    }
    sttShouldContinue = true;
    updateSttButtonLabel();
    instance.start();
  } catch (error) {
    console.warn("Unable to toggle speech recognition:", error);
    updateVoiceStatus("Khong the bat micro.", "error");
    sttShouldContinue = false;
    updateSttButtonLabel();
  }
};

const speakText = (text) => {
  if (!hasLocalTtsSupport || !ttsEnabled) return;
  const message = (text || "").trim();
  if (!message) return;
  stopServerAudio();
  try {
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(message);
    utterance.lang = "vi-VN";
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  } catch (error) {
    console.warn("Speech synthesis error:", error);
    updateVoiceStatus("Khong the doc phan hoi.", "error");
  }
};

const announceLatestAiReply = (state, options = {}) => {
  if (!state) return;
  const { preferServerTts = true } = options;
  if (preferServerTts && playLatestServerAudio()) {
    return;
  }
  const serverSegments = sessionState.lastServerTts?.segments || [];
  const derivedSegmentText = serverSegments
    .map((segment) => (segment.text ? `${segment.speaker}: ${segment.text}` : ""))
    .filter(Boolean)
    .join(" ");
  const serverText = sessionState.lastServerTts?.text || derivedSegmentText;
  if (serverText) {
    speakText(serverText);
    return;
  }
  const history = Array.isArray(state?.dialogue_history) ? state.dialogue_history : [];
  let candidate = null;
  for (let i = history.length - 1; i >= 0; i -= 1) {
    const entry = history[i];
    const content = entry?.content || entry?.text || entry?.message || "";
    if (!content) continue;
    const speaker = entry?.speaker || entry?.persona || entry?.role || "";
    if (determineRole(speaker) === "ai") {
      candidate = content;
      break;
    }
  }
  if (!candidate && state?.ai_reply) {
    candidate = state.ai_reply;
  }
  if (candidate) {
    speakText(candidate);
  }
};

const initVoiceControls = () => {
  refreshVoiceStatus();
  if (sttToggle) {
    setButtonPressed(sttToggle, false);
    updateSttButtonLabel();
    if (!hasSttSupport) {
      sttToggle.disabled = true;
      sttToggle.title = "Trinh duyet khong ho tro nhan giong.";
    }
    sttToggle.addEventListener("click", (event) => {
      event.preventDefault();
      toggleSpeechRecognition();
    });
  }
  if (ttsToggle) {
    setButtonPressed(ttsToggle, false);
    if (!hasAnyTtsSupport) {
      ttsToggle.disabled = true;
      ttsToggle.title = "Trinh duyet khong ho tro phat am thanh.";
    }
    ttsToggle.addEventListener("click", (event) => {
      event.preventDefault();
      if (!hasAnyTtsSupport) {
        updateVoiceStatus("Trinh duyet khong phat duoc phan hoi.", "error");
        return;
      }
      ttsEnabled = !ttsEnabled;
      setButtonPressed(ttsToggle, ttsEnabled);
      if (!ttsEnabled) {
        stopServerAudio();
        if (hasLocalTtsSupport && window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }
      }
      refreshVoiceStatus();
      if (ttsEnabled && sessionState?.state) {
        announceLatestAiReply(sessionState.state);
      }
    });
  }
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

const renderState = (state, options = {}) => {
  const { speakLatestAi = false, preferServerTts = true } = options;
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
  if (speakLatestAi) {
    announceLatestAiReply(state, { preferServerTts });
  }
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
  sessionState.ownerRecorded = false;
  storeServerTts(sessionPayload);
  persistSession(sessionPayload);
  updateUrlWithSession();
  ensureSessionOwnerSaved(sessionState.sessionId);
  renderState(sessionPayload.state, { speakLatestAi: ttsEnabled, preferServerTts: true });
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
      sessionState.ownerRecorded = false;
      storeServerTts(sessionPayload);
      persistSession(sessionPayload);
      updateUrlWithSession();
      ensureSessionOwnerSaved(sessionState.sessionId);
    } else {
      const turn = await sendTurn(sessionState.sessionId, value);
      sessionState.caseId = turn.case_id || sessionState.caseId;
      sessionState.state = turn.state;
      storeServerTts(turn);
      persistSession(turn);
    }
    renderState(sessionState.state, { speakLatestAi: ttsEnabled, preferServerTts: true });
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
    sessionState.ownerRecorded = false;
    storeServerTts(sessionPayload);
    persistSession(sessionPayload);
    updateUrlWithSession();
    ensureSessionOwnerSaved(sessionState.sessionId);
    renderState(sessionPayload.state, { speakLatestAi: ttsEnabled, preferServerTts: true });
  } catch (error) {
    console.error(error);
    chatHistory.innerHTML = "";
    updateSummaryPanels(null);
    appendMessage("Không thể làm mới session. Thử lại sau.", "ai");
  }
});

initVoiceControls();
document.addEventListener("DOMContentLoaded", bootstrapSession);
const markSessionOwner = async (sessionId) => {
  if (!sessionId || recordedSessions.has(sessionId)) return;
  recordedSessions.add(sessionId);
  try {
    const response = await fetch(SESSION_OWNER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!response.ok) {
      recordedSessions.delete(sessionId);
      throw new Error("Không thể cập nhật session owner.");
    }
  } catch (error) {
    recordedSessions.delete(sessionId);
    console.warn("Không thể lưu session owner:", error);
  }
};

const ensureSessionOwnerSaved = (sessionId) => {
  if (!sessionId || sessionState.ownerRecorded) return;
  markSessionOwner(sessionId).then(() => {
    if (sessionId === sessionState.sessionId) {
      sessionState.ownerRecorded = true;
    }
  });
};
