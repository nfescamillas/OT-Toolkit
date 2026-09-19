import "./styles.css";

const API = "/api/v1";
const state = { technologies: [], categories: [], favorites: new Set(), category: "", query: "", token: "" };

const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Request failed (${response.status})`);
  }
  return response.json();
}

async function signIn() {
  const result = await request("/auth/token", {
    method: "POST",
    body: JSON.stringify({ username: "demo", password: "demo-password" }),
  });
  state.token = result.access_token;
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.className = `toast visible${isError ? " error" : ""}`;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { toast.className = "toast"; }, 2800);
}

function renderCategories() {
  const items = ["", ...state.categories];
  $("#categories").innerHTML = items.map((category) => `
    <button type="button" data-category="${escapeHtml(category)}" class="${state.category === category ? "active" : ""}">
      <span>${category ? escapeHtml(category) : "All technologies"}</span>
      <b>${category ? state.technologies.filter((item) => item.category === category).length : state.technologies.length}</b>
    </button>`).join("");
  $("#categories").querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
    state.category = button.dataset.category;
    state.query = "";
    $("#search").value = "";
    renderCategories();
    renderTechnologies();
  }));
}

function visibleTechnologies() {
  const needle = state.query.toLowerCase();
  return state.technologies.filter((item) => {
    const categoryMatch = !state.category || item.category === state.category;
    const text = [item.name, item.acronym, item.overview, item.standard, ...(item.key_concepts || [])].join(" ").toLowerCase();
    return categoryMatch && (!needle || text.includes(needle));
  });
}

function renderTechnologies(onlyFavorites = false) {
  let items = visibleTechnologies();
  if (onlyFavorites) items = items.filter((item) => state.favorites.has(item.id));
  $("#collection-label").textContent = onlyFavorites ? "Saved collection" : (state.category || (state.query ? "Search results" : "All layers"));
  $("#collection-title").textContent = onlyFavorites ? "Favorites" : "Communications reference";
  $("#technology-grid").innerHTML = items.length ? items.map((item) => `
    <article class="technology-card" tabindex="0" data-id="${escapeHtml(item.id)}">
      <div class="card-top"><span>${escapeHtml(item.category)}</span><b>${state.favorites.has(item.id) ? "★" : "↗"}</b></div>
      <h3>${escapeHtml(item.name)}</h3>
      <p class="classification">${escapeHtml(item.classification)}</p>
      <p>${escapeHtml(item.overview)}</p>
      <div class="chips">${(item.key_concepts || []).slice(0, 3).map((value) => `<span>${escapeHtml(value)}</span>`).join("")}</div>
    </article>`).join("") : `<div class="empty-state">No matching technologies. Try another category or search term.</div>`;
  $("#technology-grid").querySelectorAll(".technology-card").forEach((card) => {
    const open = () => openTechnology(card.dataset.id);
    card.addEventListener("click", open);
    card.addEventListener("keydown", (event) => { if (event.key === "Enter") open(); });
  });
}

function field(label, value) {
  if (!value || (Array.isArray(value) && !value.length)) return "";
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(Array.isArray(value) ? value.join(", ") : value)}</dd></div>`;
}

function openTechnology(id) {
  const item = state.technologies.find((entry) => entry.id === id);
  if (!item) return;
  $("#detail-content").innerHTML = `
    <p class="eyebrow">${escapeHtml(item.category)}</p>
    <h2>${escapeHtml(item.name)}</h2>
    <p class="detail-class">${escapeHtml(item.classification)}</p>
    <p class="detail-overview">${escapeHtml(item.overview)}</p>
    <button type="button" class="favorite-button" data-id="${escapeHtml(item.id)}">${state.favorites.has(item.id) ? "★ Remove favorite" : "☆ Add favorite"}</button>
    <dl>${field("Architecture", item.architecture)}${field("Physical medium", item.physical_medium)}${field("Topology", item.topology)}${field("Speed", item.speed)}${field("Addressing", item.addressing)}${field("Common ports", item.ports)}${field("Configuration files", item.files)}${field("Applications", item.applications)}${field("Standard", item.standard)}</dl>`;
  $("#detail-content .favorite-button").addEventListener("click", () => toggleFavorite(item.id));
  if (!$("#detail-dialog").open) $("#detail-dialog").showModal();
}

async function toggleFavorite(id) {
  try {
    if (!state.token) await signIn();
    const enabled = !state.favorites.has(id);
    const result = await request(`/favorites/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify({ enabled }) });
    state.favorites = new Set(result.items);
    renderTechnologies();
    openTechnology(id);
    showToast(enabled ? "Saved to favorites" : "Removed from favorites");
  } catch (error) { showToast(error.message, true); }
}

function bindTool(formSelector, path, format) {
  $(formSelector).addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form));
    try {
      const result = await request(path, { method: "POST", body: JSON.stringify(payload) });
      form.querySelector("output").textContent = format(result);
    } catch (error) { form.querySelector("output").textContent = error.message; }
  });
}

async function start() {
  try {
    [state.technologies, state.categories] = await Promise.all([request("/technologies"), request("/categories")]);
    try {
      await signIn();
      state.favorites = new Set((await request("/favorites")).items);
    } catch { /* Public tools remain usable if authentication is unavailable. */ }
    $("#technology-count").textContent = state.technologies.length;
    $("#category-count").textContent = state.categories.length;
    $("#status").innerHTML = "<i></i> Backend online";
    $("#status").classList.add("online");
    renderCategories();
    renderTechnologies();
  } catch (error) {
    $("#status").textContent = "Backend unavailable";
    $("#technology-grid").innerHTML = `<div class="empty-state error-state">${escapeHtml(error.message)}</div>`;
  }
}

let searchTimer;
$("#search").addEventListener("input", (event) => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    state.query = event.target.value.trim();
    state.category = "";
    renderCategories();
    renderTechnologies();
  }, 120);
});
$("#show-favorites").addEventListener("click", () => renderTechnologies(true));
$("#detail-dialog .dialog-close").addEventListener("click", () => $("#detail-dialog").close());
$("#detail-dialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });

bindTool("#number-form", "/tools/numbers/convert", (value) => `DEC ${value.decimal}  ·  HEX ${value.hex}  ·  BIN ${value.binary}`);
bindTool("#subnet-form", "/tools/network/subnet", (value) => `Network ${value.network}/${value.cidr}\nHosts ${value.first_host} – ${value.last_host}\nBroadcast ${value.broadcast}`);
bindTool("#crc-form", "/tools/modbus/crc", (value) => `CRC ${value.crc}  ·  TX ${value.transmission_order}`);

start();
