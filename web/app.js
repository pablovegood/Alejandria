// ===========================
// Alejandría — app.js (PRO)
// ===========================

const username = localStorage.getItem("username");
const usernameSpan = document.getElementById("usernameSpan");

const resultsDiv = document.getElementById("results");
const resultsMeta = document.getElementById("resultsMeta");
const paginationDiv = document.getElementById("pagination");

const loansDiv = document.getElementById("userLoans");
const noLoansMsg = document.getElementById("noLoansMsg");

const toast = document.getElementById("message");
const loanCounterEl = document.getElementById("loanCounter");

const sortSelect = document.getElementById("sortSelect");
const clearBtn = document.getElementById("clearBtn");

const MAX_LOANS_DEFAULT = 4;

// Estado
let activeLoans = 0;
let maxLoans = MAX_LOANS_DEFAULT;

// Gutendex pagination
let currentQuery = "";
let currentPage = 1;
let totalPages = 1;
let totalCount = 0;

// Gutendex page size es 32 normalmente
const GUTEN_PAGE_SIZE = 32;

// ---------------------------
// Utils UI
// ---------------------------
function showToast(msg, type = "ok") {
  toast.textContent = msg;
  toast.className = `toast ${type === "err" ? "err" : "ok"}`;
  setTimeout(() => {
    toast.textContent = "";
    toast.className = "toast";
  }, 3200);
}

function setLoanCounter() {
  loanCounterEl.textContent = `${activeLoans}/${maxLoans}`;
  loanCounterEl.classList.toggle("full", activeLoans >= maxLoans);
}

function disableBorrowButtons(disabled) {
  document.querySelectorAll(".borrow-btn").forEach((btn) => {
    btn.disabled = disabled;
    btn.title = disabled ? `Has alcanzado el límite (${maxLoans})` : "Tomar en préstamo";
  });
}

// ---------------------------
// Sesión
// ---------------------------
if (!username) {
  window.location.href = "/static/login.html";
} else {
  usernameSpan.textContent = username;
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("username");
  window.location.href = "/static/login.html";
});

clearBtn.addEventListener("click", () => {
  document.getElementById("q").value = "";
  currentQuery = "";
  currentPage = 1;
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";
  resultsMeta.textContent = "Escribe algo y pulsa Buscar.";
});

// ---------------------------
// Préstamos
// ---------------------------
async function loadUserLoans() {
  loansDiv.innerHTML = "";
  try {
    const res = await fetch(`/loans/?username=${encodeURIComponent(username)}`);
    const data = await res.json();

    const loans = data.loans || [];
    activeLoans = data.active ?? loans.length;
    maxLoans = data.max ?? MAX_LOANS_DEFAULT;

    setLoanCounter();

    if (!loans.length) {
      noLoansMsg.style.display = "block";
      disableBorrowButtons(activeLoans >= maxLoans);
      return;
    }

    noLoansMsg.style.display = "none";

    loans.forEach((loan) => {
      const item = document.createElement("div");
      item.className = "loan-item";
      item.innerHTML = `
        <div>
          <div class="loan-title">${escapeHtml(loan.title || "Sin título")}</div>
          <div class="loan-author">${escapeHtml(loan.author || "Autor desconocido")}</div>
          <div class="loan-meta">📅 ${new Date(loan.created_at).toLocaleDateString()}</div>
        </div>
        <div class="loan-actions">
          <button class="btn-mini primary open-read" data-id="${loan.guten_id}" data-title="${escapeAttr(loan.title || "")}">
            Leer
          </button>
          <button class="btn-mini danger return-loan" data-id="${loan.guten_id}">
            Devolver
          </button>
        </div>
      `;
      loansDiv.appendChild(item);
    });

    document.querySelectorAll(".open-read").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const id = e.currentTarget.dataset.id;
        const title = e.currentTarget.dataset.title || "Libro";
        window.location.href = `/static/visor.html?id=${id}&title=${encodeURIComponent(title)}`;
      });
    });

    document.querySelectorAll(".return-loan").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        const res = await fetch(`/loans/${username}/${id}`, { method: "DELETE" });
        if (!res.ok) return showToast("No se pudo devolver el libro.", "err");
        showToast("Libro devuelto correctamente ✅");
        await loadUserLoans();
        disableBorrowButtons(activeLoans >= maxLoans);
      });
    });

    disableBorrowButtons(activeLoans >= maxLoans);
  } catch (err) {
    console.error(err);
  }
}

// ---------------------------
// Catálogo — Gutendex (paginación REAL)
// ---------------------------
async function fetchGutendex(query, page) {
  const q = query.trim();
  const url = new URL("https://gutendex.com/books/");
  if (q) url.searchParams.set("search", q);
  url.searchParams.set("page", String(page));

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Error consultando Gutendex");
  return await res.json();
}

function normalizeBook(g) {
  const author = (g.authors && g.authors.length)
    ? g.authors.map(a => a.name).join(", ")
    : "Desconocido";

  const lang = (g.languages && g.languages.length)
    ? g.languages.join(", ").toUpperCase()
    : "?";

  const downloads = g.download_count ?? 0;

  // mini descripción (no siempre viene)
  const subjects = (g.subjects && g.subjects.length) ? g.subjects.slice(0, 2).join(" · ") : "";

  return {
    guten_id: g.id,
    title: g.title || "Sin título",
    author,
    language: lang,
    downloads,
    subjects,
  };
}

function applySort(books, mode) {
  const arr = [...books];
  if (mode === "title") return arr.sort((a, b) => a.title.localeCompare(b.title));
  if (mode === "author") return arr.sort((a, b) => a.author.localeCompare(b.author));
  if (mode === "newest") return arr.sort((a, b) => (b.downloads ?? 0) - (a.downloads ?? 0));
  return arr; // relevancia = lo que venga
}

function renderBooks(books) {
  resultsDiv.innerHTML = "";

  books.forEach((b) => {
    const card = document.createElement("article");
    card.className = "book-card";
    card.innerHTML = `
      <div class="book-top">
        <span class="badge">📖 ${escapeHtml(b.language)}</span>
        <span class="badge">⬇ ${Number(b.downloads).toLocaleString()}</span>
      </div>

      <h3 class="book-title">${escapeHtml(b.title)}</h3>
      <div class="book-author">${escapeHtml(b.author)}</div>

      <p class="book-desc">
        ${b.subjects ? escapeHtml(b.subjects) : "Dominio público · Lectura inmediata · Sin registro extra"}
      </p>

      <div class="book-actions">
        <button class="btn-mini primary borrow-btn"
                data-id="${b.guten_id}"
                data-title="${escapeAttr(b.title)}"
                data-author="${escapeAttr(b.author)}">
          Tomar en préstamo
        </button>

        <button class="btn-mini open-btn"
                data-id="${b.guten_id}"
                data-title="${escapeAttr(b.title)}">
          Abrir
        </button>

        <button class="btn-mini review-write"
                data-id="${b.guten_id}"
                data-title="${escapeAttr(b.title)}">
          Reseñar
        </button>
      </div>

      <div class="accordion">
        <button class="acc-btn" data-id="${b.guten_id}">
          Reseñas
          <span>▾</span>
        </button>
        <div class="acc-content" id="acc-${b.guten_id}">
          <div class="muted">Pulsa para cargar reseñas…</div>
        </div>
      </div>
    `;

    resultsDiv.appendChild(card);
  });

  // Botones: abrir
  document.querySelectorAll(".open-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const id = e.currentTarget.dataset.id;
      const title = e.currentTarget.dataset.title || "Libro";
      window.location.href = `/static/visor.html?id=${id}&title=${encodeURIComponent(title)}`;
    });
  });

  // Botones: prestar
  document.querySelectorAll(".borrow-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const b = e.currentTarget;

      if (activeLoans >= maxLoans) {
        showToast(`Límite alcanzado: máximo ${maxLoans} préstamos.`, "err");
        disableBorrowButtons(true);
        return;
      }

      b.disabled = true;
      const guten_id = b.dataset.id;
      const title = b.dataset.title;
      const author = b.dataset.author;

      try {
        const res = await fetch("/loans/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, guten_id, title, author }),
        });

        let body = {};
        try { body = await res.json(); } catch {}

        if (res.status === 403) {
          showToast(body.detail || `No puedes tener más de ${maxLoans} libros.`, "err");
          await loadUserLoans();
          return;
        }

        if (res.status === 409) {
          showToast(body.detail || "Este libro no está disponible o ya lo tienes.", "err");
          await loadUserLoans();
          return;
        }

        if (!res.ok) {
          showToast(body.detail || "Error al tomar el préstamo.", "err");
          await loadUserLoans();
          return;
        }

        showToast(`Añadido: "${title}" ✅`, "ok");
        await loadUserLoans();
      } finally {
        disableBorrowButtons(activeLoans >= maxLoans);
      }
    });
  });

  // Botones: reseñar
  document.querySelectorAll(".review-write").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const id = e.currentTarget.dataset.id;
      const title = e.currentTarget.dataset.title || "Libro";
      writeReview(id, title);
    });
  });

  // Accordion: reseñas (solo al click)
  document.querySelectorAll(".acc-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const id = e.currentTarget.dataset.id;
      const content = document.getElementById(`acc-${id}`);

      const isOpen = content.classList.contains("open");
      if (isOpen) {
        content.classList.remove("open");
        return;
      }

      content.classList.add("open");

      // Si ya cargó reseñas antes, no repetir
      if (content.dataset.loaded === "true") return;

      content.innerHTML = `<div class="muted">Cargando reseñas…</div>`;
      await loadReviews(id);
    });
  });

  disableBorrowButtons(activeLoans >= maxLoans);
}

function renderPagination() {
  paginationDiv.innerHTML = "";

  const mkBtn = (label, page, disabled = false, active = false) => {
    const b = document.createElement("button");
    b.className = `page-btn ${active ? "active" : ""}`;
    b.textContent = label;
    b.disabled = disabled;
    b.addEventListener("click", () => goToPage(page));
    return b;
  };

  const addEllipsis = () => {
    const s = document.createElement("span");
    s.className = "page-ellipsis";
    s.textContent = "…";
    paginationDiv.appendChild(s);
  };

  // First / Prev
  paginationDiv.appendChild(mkBtn("⟪", 1, currentPage === 1));
  paginationDiv.appendChild(mkBtn("⟨", Math.max(1, currentPage - 1), currentPage === 1));

  // Ventana de páginas
  const windowSize = 7;
  let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
  let end = Math.min(totalPages, start + windowSize - 1);
  start = Math.max(1, end - windowSize + 1);

  if (start > 1) addEllipsis();

  for (let p = start; p <= end; p++) {
    paginationDiv.appendChild(mkBtn(String(p), p, false, p === currentPage));
  }

  if (end < totalPages) addEllipsis();

  // Next / Last
  paginationDiv.appendChild(mkBtn("⟩", Math.min(totalPages, currentPage + 1), currentPage === totalPages));
  paginationDiv.appendChild(mkBtn("⟫", totalPages, currentPage === totalPages));
}

async function goToPage(page) {
  currentPage = page;
  await searchBooks(currentQuery, currentPage);
}

async function searchBooks(query, page = 1) {
  currentQuery = query.trim();
  currentPage = page;

  resultsMeta.textContent = "Buscando…";
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";

  try {
    const json = await fetchGutendex(currentQuery, currentPage);

    totalCount = json.count || 0;
    totalPages = Math.max(1, Math.ceil(totalCount / GUTEN_PAGE_SIZE));

    let books = (json.results || []).map(normalizeBook);

    // Orden (solo en cliente)
    books = applySort(books, sortSelect.value);

    resultsMeta.textContent = totalCount
      ? `Mostrando página ${currentPage} de ${totalPages} · ${totalCount.toLocaleString()} resultados`
      : "Sin resultados.";

    renderBooks(books);
    renderPagination();
  } catch (err) {
    console.error(err);
    resultsMeta.textContent = "No se pudieron cargar resultados.";
  }
}

sortSelect.addEventListener("change", async () => {
  await searchBooks(currentQuery, currentPage);
});

// ---------------------------
// Reseñas (backend tuyo)
// ---------------------------
async function writeReview(guten_id, title) {
  const rating = prompt(`Puntuación (1–5) para "${title}":`);
  if (!rating || isNaN(rating) || rating < 1 || rating > 5) return;

  const text = prompt("Escribe tu reseña:") || "";

  const res = await fetch(`/reviews/${guten_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, rating: parseInt(rating), text }),
  });

  if (!res.ok) return showToast("Error al enviar reseña.", "err");

  showToast("Reseña enviada ✅", "ok");

  // Si el accordion estaba abierto, refrescamos
  await loadReviews(guten_id, true);
}

async function loadReviews(guten_id, forceOpen = false) {
  const content = document.getElementById(`acc-${guten_id}`);
  if (!content) return;

  if (forceOpen) content.classList.add("open");

  try {
    const res = await fetch(`/reviews/${guten_id}`);
    if (!res.ok) throw new Error("Error al cargar reseñas");
    const reviews = await res.json();

    if (!reviews || !reviews.length) {
      content.innerHTML = `<div class="muted">Sin reseñas todavía.</div>`;
      content.dataset.loaded = "true";
      return;
    }

    content.innerHTML = reviews.map(r => `
      <div class="review-item">
        <p class="review-meta">⭐ ${r.rating} — ${escapeHtml(r.username)} · ${new Date(r.created_at).toLocaleDateString()}</p>
        <p class="review-text">${escapeHtml(r.text || "")}</p>
      </div>
    `).join("");

    content.dataset.loaded = "true";
  } catch {
    content.innerHTML = `<div class="muted">No se pudieron cargar reseñas.</div>`;
  }
}

// ---------------------------
// Seguridad (escape HTML)
// ---------------------------
function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
function escapeAttr(s) {
  return escapeHtml(s).replaceAll("\n", " ");
}

// ---------------------------
// Init
// ---------------------------
document.getElementById("searchForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  searchBooks(q, 1);
});

window.onload = async () => {
  await loadUserLoans();
  // default: muestra algo bonito sin buscar
  searchBooks("", 1);
};
