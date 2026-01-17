let adminAuth = null;

const statusEl = document.getElementById("status");
const adminForm = document.getElementById("adminForm");

const usersListEl = document.getElementById("usersList");
const reviewsListEl = document.getElementById("reviewsList");
const bookListEl = document.getElementById("bookList");

const userSearchEl = document.getElementById("userSearch");
const reviewSearchEl = document.getElementById("reviewSearch");

const usersPrevBtn = document.getElementById("usersPrev");
const usersNextBtn = document.getElementById("usersNext");
const usersPageInfo = document.getElementById("usersPageInfo");

const reviewsPrevBtn = document.getElementById("reviewsPrev");
const reviewsNextBtn = document.getElementById("reviewsNext");
const reviewsPageInfo = document.getElementById("reviewsPageInfo");

let usersOffset = 0;
let reviewsOffset = 0;
const PAGE_SIZE = 50;

function setStatus(msg, ok = true) {
  statusEl.textContent = msg;
  statusEl.style.color = ok ? "rgba(248,248,248,.85)" : "rgba(255,120,120,.95)";
}

function buildAuth(user, pass) {
  return "Basic " + btoa(`${user}:${pass}`);
}

async function ping() {
  const res = await fetch("/admin/ping", {
    headers: { Authorization: adminAuth }
  });
  return res.ok;
}

function debounce(fn, ms=350){
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// =========================
// BOOKS
// =========================
async function refreshBooks() {
  bookListEl.textContent = "Cargando…";

  const res = await fetch("/admin/books", { headers: { Authorization: adminAuth }});
  if (!res.ok) {
    bookListEl.textContent = "No se pudieron cargar los libros.";
    return;
  }

  const data = await res.json();
  if (!data.length) {
    bookListEl.textContent = "No hay libros añadidos.";
    return;
  }

  bookListEl.innerHTML = data.map(b => `
    <div class="item">
      <div class="item-top">
        <div><b>${escapeHTML(b.title)}</b> — <span style="opacity:.8">${escapeHTML(b.author || "Desconocido")}</span></div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button class="btn danger" onclick="deleteBook(${b.id})">Eliminar</button>
        </div>
      </div>
      <div class="item-meta">
        ID: ${b.id} · ${new Date(b.created_at).toLocaleString()}
        · PDF: ${b.has_pdf ? "✅" : "❌"} · TXT: ${b.has_txt ? "✅" : "❌"}
      </div>
    </div>
  `).join("");
}

window.deleteBook = async function(id){
  const res = await fetch(`/admin/books/${id}`, {
    method: "DELETE",
    headers: { Authorization: adminAuth }
  });
  if (!res.ok) return setStatus("No se pudo borrar el libro.", false);
  setStatus("Libro eliminado ✅", true);
  refreshBooks();
}

// =========================
// USERS (list + search)
// =========================
async function refreshUsers() {
  usersListEl.textContent = "Cargando…";

  const q = userSearchEl.value.trim();
  const url = `/admin/users?q=${encodeURIComponent(q)}&limit=${PAGE_SIZE}&offset=${usersOffset}`;

  const res = await fetch(url, { headers: { Authorization: adminAuth }});
  if (!res.ok) {
    usersListEl.textContent = "No se pudieron cargar los usuarios.";
    return;
  }

  const data = await res.json();
  const items = data.items || [];
  const total = data.total ?? items.length;

  usersPageInfo.textContent = `${usersOffset + 1}-${Math.min(usersOffset + PAGE_SIZE, total)} de ${total}`;

  usersPrevBtn.disabled = usersOffset <= 0;
  usersNextBtn.disabled = (usersOffset + PAGE_SIZE) >= total;

  if (!items.length) {
    usersListEl.innerHTML = `<div class="muted">No hay usuarios que coincidan.</div>`;
    return;
  }

  usersListEl.innerHTML = items.map(u => `
    <div class="item">
      <div class="item-top">
        <div><b>@${escapeHTML(u.username)}</b></div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button class="btn danger" onclick="deleteUser('${escapeAttr(u.username)}')">Eliminar</button>
        </div>
      </div>
      <div class="item-meta">
        Esta acción borra también sus reseñas y devuelve sus préstamos.
      </div>
    </div>
  `).join("");
}

window.deleteUser = async function(username){
  if (!confirm(`¿Eliminar usuario "${username}"?\n\nEsto borrará sus reseñas y devolverá sus préstamos.`)) return;

  const res = await fetch(`/admin/users/${encodeURIComponent(username)}`, {
    method: "DELETE",
    headers: { Authorization: adminAuth }
  });

  if (!res.ok) return setStatus("No se pudo eliminar el usuario.", false);

  const data = await res.json();
  setStatus(`Usuario eliminado ✅ (reseñas: ${data.deleted_reviews}, préstamos devueltos: ${data.returned_loans})`);

  // recargar ambos listados (porque cambian)
  await refreshUsers();
  await refreshReviews();
}

// =========================
// REVIEWS (list + search)
// =========================
function renderStars(n){
  const k = Number.isFinite(n) ? Math.max(0, Math.min(5, n)) : null;
  return k === null ? "" : "⭐".repeat(k);
}

async function refreshReviews() {
  reviewsListEl.textContent = "Cargando…";

  const q = reviewSearchEl.value.trim();
  const url = `/admin/reviews?q=${encodeURIComponent(q)}&limit=${PAGE_SIZE}&offset=${reviewsOffset}`;

  const res = await fetch(url, { headers: { Authorization: adminAuth }});
  if (!res.ok) {
    reviewsListEl.textContent = "No se pudieron cargar las reseñas.";
    return;
  }

  const data = await res.json();
  const items = data.items || [];
  const total = data.total ?? items.length;

  reviewsPageInfo.textContent = `${reviewsOffset + 1}-${Math.min(reviewsOffset + PAGE_SIZE, total)} de ${total}`;

  reviewsPrevBtn.disabled = reviewsOffset <= 0;
  reviewsNextBtn.disabled = (reviewsOffset + PAGE_SIZE) >= total;

  if (!items.length) {
    reviewsListEl.innerHTML = `<div class="muted">No hay reseñas que coincidan.</div>`;
    return;
  }

  reviewsListEl.innerHTML = items.map(r => `
    <div class="item">
      <div class="item-top">
        <div>
          <b>#${r.id}</b> · <span style="opacity:.9">@${escapeHTML(r.username)}</span>
          ${r.guten_id !== undefined ? `<span style="opacity:.7">· Book ID: ${r.guten_id}</span>` : ""}
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button class="btn danger" onclick="deleteReview(${r.id})">Eliminar</button>
        </div>
      </div>

      <div class="item-meta">
        ${r.rating !== undefined ? renderStars(r.rating) : ""}
        ${r.created_at ? `· ${new Date(r.created_at).toLocaleString()}` : ""}
      </div>

      <div style="margin-top:8px;line-height:1.35;opacity:.92;">
        ${escapeHTML(r.text || "")}
      </div>
    </div>
  `).join("");
}

window.deleteReview = async function(id){
  if (!confirm(`¿Eliminar reseña #${id}?`)) return;

  const res = await fetch(`/admin/reviews/${id}`, {
    method: "DELETE",
    headers: { Authorization: adminAuth }
  });

  if (!res.ok) return setStatus("No se pudo eliminar la reseña.", false);

  setStatus("Reseña eliminada ✅");
  refreshReviews();
}

// =========================
// Upload PDF
// =========================
document.getElementById("uploadBookBtn").addEventListener("click", async (e) => {
  e.preventDefault();
  if (!adminAuth) return setStatus("Primero haz login admin.", false);

  const title = document.getElementById("bookTitle").value.trim();
  const author = document.getElementById("bookAuthor").value.trim();
  const language = document.getElementById("bookLang").value.trim();
  const fileInput = document.getElementById("bookPdf");

  if (!title) return setStatus("El título es obligatorio.", false);
  if (!fileInput.files || !fileInput.files.length) return setStatus("Selecciona un PDF.", false);

  const pdf = fileInput.files[0];
  if (!pdf.name.toLowerCase().endsWith(".pdf")) return setStatus("Solo se aceptan PDFs.", false);

  setStatus("Subiendo PDF y extrayendo texto…");

  const fd = new FormData();
  fd.append("title", title);
  fd.append("author", author);
  fd.append("language", language);
  fd.append("pdf", pdf);

  const res = await fetch("/admin/books/upload", {
    method: "POST",
    headers: { Authorization: adminAuth },
    body: fd
  });

  if (!res.ok) {
    const msg = await res.text();
    return setStatus("Error subiendo PDF ❌ " + msg, false);
  }

  const data = await res.json();
  setStatus(`Libro añadido ✅ (id: ${data.id}, chars: ${data.extracted_chars})`);

  fileInput.value = "";
  refreshBooks();
});

// =========================
// Login flow
// =========================
adminForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const u = document.getElementById("adminUser").value.trim();
  const p = document.getElementById("adminPass").value.trim();

  if (!u || !p) return setStatus("Rellena usuario y contraseña.", false);

  adminAuth = buildAuth(u, p);

  const ok = await ping();
  if (!ok) {
    setStatus("Credenciales incorrectas o admin desactivado ❌", false);
    adminAuth = null;
    return;
  }

  setStatus("Login admin correcto ✅");

  // cargar todo
  usersOffset = 0;
  reviewsOffset = 0;
  await refreshUsers();
  await refreshReviews();
  await refreshBooks();
});

// =========================
// Search handlers
// =========================
document.getElementById("reloadUsersBtn").addEventListener("click", () => {
  usersOffset = 0;
  refreshUsers();
});

document.getElementById("reloadReviewsBtn").addEventListener("click", () => {
  reviewsOffset = 0;
  refreshReviews();
});

userSearchEl.addEventListener("input", debounce(() => {
  usersOffset = 0;
  refreshUsers();
}, 300));

reviewSearchEl.addEventListener("input", debounce(() => {
  reviewsOffset = 0;
  refreshReviews();
}, 300));

// =========================
// Pagination controls
// =========================
usersPrevBtn.addEventListener("click", () => {
  usersOffset = Math.max(0, usersOffset - PAGE_SIZE);
  refreshUsers();
});
usersNextBtn.addEventListener("click", () => {
  usersOffset += PAGE_SIZE;
  refreshUsers();
});

reviewsPrevBtn.addEventListener("click", () => {
  reviewsOffset = Math.max(0, reviewsOffset - PAGE_SIZE);
  refreshReviews();
});
reviewsNextBtn.addEventListener("click", () => {
  reviewsOffset += PAGE_SIZE;
  refreshReviews();
});

// =========================
// tiny safe escaping
// =========================
function escapeHTML(s){
  return String(s ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}
function escapeAttr(s){
  return escapeHTML(s).replaceAll('"',"&quot;");
}
