const grid = document.getElementById("case-grid");
const emptyState = document.getElementById("case-empty");
const caseCount = document.getElementById("case-count");
const searchInput = document.getElementById("case-search");
const filterSelect = document.getElementById("case-filter");

const state = {
  cases: [],
  filtered: []
};

const formatTag = (value) => {
  if (!value) return "Khác";
  return value.toString().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
};

const buildCard = (item) => {
  const anchor = document.createElement("a");
  anchor.className = "group flex flex-col gap-3 rounded-2xl border border-slate-100 bg-white/90 p-5 shadow-card transition hover:-translate-y-1 hover:border-primary-200 hover:shadow-lg";
  anchor.href = `/chatframe?case_id=${encodeURIComponent(item.case_id || "")}`;
  anchor.setAttribute("data-status", (item.status || "queued").toLowerCase());
  anchor.setAttribute("data-topic", (item.topic || "").toLowerCase());
  anchor.setAttribute("data-case-id", (item.case_id || "").toLowerCase());

  const badge = document.createElement("span");
  badge.className = "inline-flex w-fit items-center gap-2 rounded-full border border-primary-100 bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-600";
  badge.textContent = item.case_id || "Case";
  anchor.appendChild(badge);

  const title = document.createElement("h3");
  title.className = "text-lg font-semibold text-slate-900 group-hover:text-primary-600";
  title.textContent = item.topic || "Chưa có tiêu đề";
  anchor.appendChild(title);

  const desc = document.createElement("p");
  desc.className = "line-clamp-3 text-sm text-slate-600";
  desc.textContent = item.summary || "Chưa có mô tả cho case này.";
  anchor.appendChild(desc);

  const meta = document.createElement("div");
  meta.className = "case-meta";
  if (item.location) meta.appendChild(document.createElement("span")).textContent = item.location;
  if (item.time) meta.appendChild(document.createElement("span")).textContent = item.time;
  if (item.status) meta.appendChild(document.createElement("span")).textContent = formatTag(item.status);
  if (meta.childElementCount) anchor.appendChild(meta);

  // Track if already navigating to prevent duplicate clicks
  let isNavigating = false;
  
  anchor.addEventListener("click", (event) => {
    if (!item.case_id) return;
    
    // Prevent duplicate clicks
    if (isNavigating) {
      event.preventDefault();
      return;
    }
    
    event.preventDefault();
    isNavigating = true;
    anchor.classList.add("pointer-events-none", "opacity-50");
    
    // Navigate to chatframe - session will be created there
    window.location.href = `/chatframe?case_id=${encodeURIComponent(item.case_id)}`;
  });

  return anchor;
};

const render = () => {
  if (!grid) return;
  grid.innerHTML = "";

  if (!state.filtered.length) {
    emptyState?.classList.remove("hidden");
    if (caseCount) caseCount.textContent = "0 case";
    return;
  }

  emptyState?.classList.add("hidden");
  state.filtered.forEach((item) => grid.appendChild(buildCard(item)));
  if (caseCount) caseCount.textContent = `${state.filtered.length} case`;
};

const applyFilter = () => {
  const query = (searchInput?.value || "").toLowerCase().trim();
  const status = filterSelect?.value || "all";

  state.filtered = state.cases.filter((item) => {
    const matchesQuery = !query ||
      (item.topic || "").toLowerCase().includes(query) ||
      (item.case_id || "").toLowerCase().includes(query);
    const matchesStatus = status === "all" || (item.status || "queued").toLowerCase() === status;
    return matchesQuery && matchesStatus;
  });

  render();
};

const loadCases = async () => {
  try {
    const response = await fetch("/api/cases");
    if (!response.ok) throw new Error(`Fetch failed with ${response.status}`);
    const data = await response.json();
    state.cases = Array.isArray(data?.cases) ? data.cases : [];
    state.filtered = [...state.cases];
    render();
  } catch (error) {
    console.error(error);
    state.cases = [];
    state.filtered = [];
    render();
  }
};

searchInput?.addEventListener("input", applyFilter);
filterSelect?.addEventListener("change", applyFilter);

document.addEventListener("DOMContentLoaded", loadCases);
