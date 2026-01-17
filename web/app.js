const username = localStorage.getItem("username");
const usernameSpan = document.getElementById("usernameSpan");

const resultsMeta = document.getElementById("resultsMeta");
const resultsDiv = document.getElementById("results");
const paginationDiv = document.getElementById("pagination");

const loansDiv = document.getElementById("userLoans");
const messageDiv = document.getElementById("message");
const noLoansMsg = document.getElementById("noLoansMsg");
const loanCounterSpan = document.getElementById("loanCounter");

const sortSelect = document.getElementById("sortSelect");
const clearBtn = document.getElementById("clearBtn");

let activeLoans = 0;
let maxLoans = 4;
let loanedIds = new Set();

// Estado catálogo/paginación
let lastQuery = "";
let currentPage = 1;

// Fallback local (si backend no soporta page)
const localPageSize = 8;
let lastBooksArray = null; // si backend devuelve array (sin count/next)


// ===========================
// 🔐 Sesión
// ===========================
if (!username) {
  alert("⚠️ No hay sesión activa. Inicia sesión.");
  window.location.href = "/static/login.html";
} else {
  usernameSpan.textContent = username;
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("username");
  window.location.href = "/static/login.html";
});


// ===========================
// 💬 Mensajes (toast)
// ===========================
function showMessage(text, isError = false) {
  if (!messageDiv) return;
  messageDiv.textContent = text;
  messageDiv.classList.remove("ok", "err");
  messageDiv.classList.add(isError ? "err" : "ok");

  window.clearTimeout(showMessage._t);
  showMessage._t = window.setTimeout(() => {
    messageDiv.textContent = "";
    messageDiv.classList.remove("ok", "err");
  }, 3200);
}


// ===========================
// 📌 Estado préstamos -> botones de préstamo
// ===========================
function updateBorrowButtonsState() {
  const isFull = activeLoans >= maxLoans;

  document.querySelectorAll(".loan-btn").forEach((btn) => {
    const id = btn.dataset.id;
    const alreadyLoaned = loanedIds.has(String(id));

    btn.disabled = isFull || alreadyLoaned;

    if (alreadyLoaned) {
      btn.title = "Ya tienes este libro en préstamo.";
    } else if (isFull) {
      btn.title = `Has alcanzado el límite de préstamos (${maxLoans}). Devuelve uno para pedir otro.`;
    } else {
      btn.title = "📚 Tomar en préstamo";
    }
  });

  // contador lateral
  if (loanCounterSpan) {
    loanCounterSpan.textContent = `${activeLoans}/${maxLoans}`;
  }
}


// ===========================
// 📚 Préstamos (sidebar)
// ===========================
async function loadUserLoans() {
  loansDiv.innerHTML = "";
  loanedIds = new Set();

  try {
    const res = await fetch(`/loans/?username=${encodeURIComponent(username)}`);
    const data = await res.json();

    const loans = Array.isArray(data) ? data : (data.loans || []);

    activeLoans =
      typeof data.active_count === "number"
        ? data.active_count
        : typeof data.active === "number"
        ? data.active
        : loans.length;

    maxLoans =
      typeof data.max_loans === "number"
        ? data.max_loans
        : typeof data.max === "number"
        ? data.max
        : 4;

    // Guardar IDs prestados
    loans.forEach((l) => loanedIds.add(String(l.guten_id)));

    // contador lateral + botones
    updateBorrowButtonsState();

    if (!loans.length) {
      noLoansMsg.style.display = "block";
      return;
    }

    noLoansMsg.style.display = "none";

    loans.forEach((loan) => {
      const item = document.createElement("div");
      item.classList.add("loan-item");

      const created = loan.created_at ? new Date(loan.created_at).toLocaleDateString() : "";

      item.innerHTML = `
        <div class="loan-info">
          <div class="loan-title">${escapeHtml(loan.title)}</div>
          <div class="loan-author">${escapeHtml(loan.author || "")}</div>
          <div class="loan-meta">📅 ${created}</div>
        </div>
        <div class="loan-actions">
          <button class="btn-mini primary open-visor-btn"
                  data-id="${loan.guten_id}"
                  data-title="${escapeAttr(loan.title)}">
            📖 Leer
          </button>
          <button class="btn-mini danger return-btn"
                  data-id="${loan.guten_id}">
            ↩ Devolver
          </button>
        </div>
      `;

      loansDiv.appendChild(item);
    });

    // Abrir visor
    document.querySelectorAll(".open-visor-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const id = e.currentTarget.dataset.id;
        const title = e.currentTarget.dataset.title;
        window.location.href = `/static/visor.html?id=${id}&title=${encodeURIComponent(title)}`;
      });
    });

    // Devolver
    document.querySelectorAll(".return-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;

        const r = await fetch(`/loans/${encodeURIComponent(username)}/${encodeURIComponent(id)}`, {
          method: "DELETE",
        });

        if (!r.ok) {
          showMessage("❌ Error al devolver el libro.", true);
          return;
        }

        showMessage("↩ Libro devuelto correctamente.");
        await loadUserLoans();
        // refrescar estado botones del catálogo
        updateBorrowButtonsState();
      });
    });
  } catch (err) {
    console.error("Error cargando préstamos:", err);
    // deja contador consistente
    activeLoans = 0;
    maxLoans = maxLoans || 4;
    updateBorrowButtonsState();
  }
}


// ===========================
// 🔍 Buscar / Paginar catálogo
// ===========================
async function fetchCatalog(query, page) {
  // Intento 1: backend paginado
  const url = `/catalog/search?q=${encodeURIComponent(query || "")}&page=${encodeURIComponent(page)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("catalog search failed");
  return await res.json();
}

function applySort(books, mode) {
  const arr = [...books];

  if (mode === "title") {
    arr.sort((a, b) => (a.title || "").localeCompare(b.title || "", "es"));
  } else if (mode === "author") {
    arr.sort((a, b) => (a.author || "").localeCompare(b.author || "", "es"));
  } else if (mode === "newest") {
    // en gutendex esto suele ser "download_count"
    arr.sort((a, b) => (b.download_count || 0) - (a.download_count || 0));
  } // relevance: no tocamos

  return arr;
}

async function searchBooks(query = "", page = 1) {
  lastQuery = query;
  currentPage = page;

  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";
  resultsMeta.textContent = "Buscando…";

  try {
    const data = await fetchCatalog(query, page);

    // Caso A: Gutendex-like -> { count, next, previous, results: [...] }
    if (data && Array.isArray(data.results)) {
      lastBooksArray = null;
      const total = Number.isFinite(data.count) ? data.count : null;
      const books = applySort(data.results, sortSelect.value);

      renderResultsPaged(books, {
        totalCount: total,
        page: page,
        pageSizeGuess: books.length || 1,
        hasNext: !!data.next,
        hasPrev: !!data.previous,
      });

      return;
    }

    // Caso B: backend devuelve array directamente
    if (Array.isArray(data)) {
      lastBooksArray = applySort(data, sortSelect.value);
      renderResultsLocal(lastBooksArray, page);
      return;
    }

    // Caso C: backend devuelve {results: [...] } pero sin count/next
    if (data && Array.isArray(data.results)) {
      lastBooksArray = applySort(data.results, sortSelect.value);
      renderResultsLocal(lastBooksArray, page);
      return;
    }

    resultsMeta.textContent = "No se encontraron resultados.";
    resultsDiv.innerHTML = "";
  } catch (err) {
    console.error(err);
    resultsMeta.textContent = "⚠️ Error al buscar libros.";
    resultsDiv.innerHTML = "";
  }
}


// ===========================
// 🧱 Render: paginado backend (página actual)
// ===========================
function renderResultsPaged(books, meta) {
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";

  if (!books.length) {
    resultsMeta.textContent = "No se encontraron resultados.";
    return;
  }

  const totalText = meta.totalCount ? ` · ${meta.totalCount} resultados` : "";
  resultsMeta.textContent = `Mostrando página ${meta.page}${totalText}`;

  books.forEach((book) => resultsDiv.appendChild(buildBookCard(book)));

  // Paginación (prev/next + números acotados)
  const prevBtn = makePageBtn("⬅ Anterior", meta.page - 1, meta.page === 1);
  const nextBtn = makePageBtn("Siguiente ➡", meta.page + 1, !meta.hasNext);

  paginationDiv.appendChild(prevBtn);

  // Números (ventana)
  const windowSize = 7;
  const start = Math.max(1, meta.page - Math.floor(windowSize / 2));
  const end = meta.totalCount
    ? Math.min(start + windowSize - 1, Math.ceil(meta.totalCount / Math.max(1, meta.pageSizeGuess)))
    : meta.page + 3;

  for (let p = start; p <= end; p++) {
    const b = makePageBtn(String(p), p, false, p === meta.page);
    paginationDiv.appendChild(b);
  }

  paginationDiv.appendChild(nextBtn);

  // estado botones préstamo
  updateBorrowButtonsState();
}


// ===========================
// 🧱 Render: fallback local (si backend no pagina)
// ===========================
function renderResultsLocal(allBooks, page) {
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";

  if (!allBooks || !allBooks.length) {
    resultsMeta.textContent = "No se encontraron resultados.";
    return;
  }

  const totalPages = Math.max(1, Math.ceil(allBooks.length / localPageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  currentPage = safePage;

  const start = (safePage - 1) * localPageSize;
  const end = start + localPageSize;
  const pageBooks = allBooks.slice(start, end);

  resultsMeta.textContent = `Mostrando página ${safePage} de ${totalPages} · ${allBooks.length} resultados`;

  pageBooks.forEach((book) => resultsDiv.appendChild(buildBookCard(book)));

  const prevBtn = makePageBtn("⬅ Anterior", safePage - 1, safePage === 1);
  const nextBtn = makePageBtn("Siguiente ➡", safePage + 1, safePage === totalPages);

  paginationDiv.appendChild(prevBtn);

  for (let p = 1; p <= totalPages; p++) {
    const b = makePageBtn(String(p), p, false, p === safePage);
    paginationDiv.appendChild(b);
  }

  paginationDiv.appendChild(nextBtn);

  updateBorrowButtonsState();
}


// ===========================
// 🧩 Book card (incluye desplegable de reseñas)
// ===========================
function buildBookCard(book) {
  const div = document.createElement("div");
  div.className = "book-card";

  const lang = book.language || "?";
  const downloads = book.download_count ? `${book.download_count} desc.` : null;

  div.innerHTML = `
    <div class="book-top">
      <div class="badge">🌐 ${escapeHtml(lang)}</div>
      ${downloads ? `<div class="badge">⬇ ${escapeHtml(String(downloads))}</div>` : ""}
    </div>

    <h3 class="book-title">${escapeHtml(book.title || "Sin título")}</h3>
    <div class="book-author"><em>${escapeHtml(book.author || "Autor desconocido")}</em></div>

    <p class="book-desc">${escapeHtml(shorten(book.subject || book.summary || "", 140))}</p>

    <div class="book-actions">
      <button class="loan-btn btn-mini primary"
              data-id="${book.guten_id}"
              data-title="${escapeAttr(book.title || "")}"
              data-author="${escapeAttr(book.author || "")}">
        📚 Tomar en préstamo
      </button>

      <button class="btn-mini"
              data-action="write-review"
              data-id="${book.guten_id}"
              data-title="${escapeAttr(book.title || "")}">
        📝 Reseñar
      </button>

      <button class="btn-mini"
              data-action="open-visor"
              data-id="${book.guten_id}"
              data-title="${escapeAttr(book.title || "")}">
        📖 Leer
      </button>
    </div>

    <div class="accordion">
      <button class="acc-btn" data-action="toggle-reviews" data-id="${book.guten_id}">
        <span>Reseñas</span>
        <span>▾</span>
      </button>

      <div class="acc-content" id="reviews-${book.guten_id}">
        <div class="muted">Pulsa para cargar reseñas…</div>
      </div>
    </div>
  `;

  // handlers
  const loanBtn = div.querySelector(".loan-btn");
  loanBtn.addEventListener("click", () => takeLoan(book));

  div.querySelector('[data-action="write-review"]').addEventListener("click", () => {
    writeReview(book.guten_id, book.title || "Sin título");
  });

  div.querySelector('[data-action="open-visor"]').addEventListener("click", () => {
    window.location.href = `/static/visor.html?id=${book.guten_id}&title=${encodeURIComponent(book.title || "")}`;
  });

  div.querySelector('[data-action="toggle-reviews"]').addEventListener("click", async () => {
    const container = div.querySelector(`#reviews-${book.guten_id}`);
    const isOpen = container.classList.contains("open");

    // toggle
    container.classList.toggle("open", !isOpen);

    // cargar solo la primera vez que se abre
    if (!isOpen && !container.dataset.loaded) {
      await loadReviews(book.guten_id, container);
      container.dataset.loaded = "1";
    }
  });

  return div;
}


// ===========================
// 📚 Tomar préstamo
// ===========================
async function takeLoan(book) {
  const id = String(book.guten_id);

  if (loanedIds.has(id)) {
    showMessage("⚠️ Ya tienes este libro en préstamo.", true);
    return;
  }

  if (activeLoans >= maxLoans) {
    showMessage(`⚠️ Has alcanzado el límite de ${maxLoans} préstamos.`, true);
    updateBorrowButtonsState();
    return;
  }

  const res = await fetch("/loans/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      guten_id: book.guten_id,
      title: book.title,
      author: book.author,
    }),
  });

  if (res.status === 403 || res.status === 409) {
    try {
      const payload = await res.json();
      showMessage(`⚠️ ${payload.detail || "No se pudo tomar el préstamo."}`, true);
    } catch {
      showMessage("⚠️ No se pudo tomar el préstamo.", true);
    }
    await loadUserLoans();
    updateBorrowButtonsState();
    return;
  }

  if (!res.ok) {
    showMessage("❌ Error al tomar el préstamo.", true);
    return;
  }

  showMessage(`✅ "${book.title}" añadido a tus préstamos.`);
  await loadUserLoans();
  updateBorrowButtonsState();
}


// ===========================
// 📝 Reseñas
// ===========================
async function writeReview(guten_id, title) {
  const ratingStr = prompt(`Puntuación (1–5 estrellas) para "${title}":`);
  if (!ratingStr) return;

  const rating = parseInt(ratingStr, 10);
  if (Number.isNaN(rating) || rating < 1 || rating > 5) return;

  const text = prompt("Escribe tu reseña:") || "";

  const res = await fetch(`/reviews/${encodeURIComponent(guten_id)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, rating, text }),
  });

  if (!res.ok) {
    showMessage("❌ Error al enviar reseña.", true);
    return;
  }

  showMessage("📝 Reseña enviada.");

  // si el desplegable está abierto, recargarlo
  const container = document.getElementById(`reviews-${guten_id}`);
  if (container && container.classList.contains("open")) {
    await loadReviews(guten_id, container, true);
    container.dataset.loaded = "1";
  } else if (container) {
    // si no está abierto, al menos marca como no-cargado para que se vea nuevo al abrir
    container.dataset.loaded = "";
    container.innerHTML = `<div class="muted">Pulsa para cargar reseñas…</div>`;
  }
}

async function loadReviews(guten_id, container, force = false) {
  if (!container) container = document.getElementById(`reviews-${guten_id}`);
  if (!container) return;

  if (!force) {
    container.innerHTML = `<div class="muted">Cargando reseñas…</div>`;
  }

  try {
    const res = await fetch(`/reviews/${encodeURIComponent(guten_id)}`);
    if (!res.ok) throw new Error("reviews failed");

    const data = await res.json();
    const reviews = Array.isArray(data) ? data : (data.reviews || []);

    container.innerHTML = reviews.length
      ? reviews
          .map((r) => {
            const created = r.created_at ? new Date(r.created_at).toLocaleDateString() : "";
            return `
              <div class="review-item">
                <p class="review-meta">⭐${escapeHtml(String(r.rating))} — ${escapeHtml(r.username)} (${escapeHtml(created)})</p>
                <p class="review-text">${escapeHtml(r.text || "")}</p>
              </div>
            `;
          })
          .join("")
      : `<div class="muted">Sin reseñas aún.</div>`;
  } catch (e) {
    container.innerHTML = `<div class="muted">No se pudieron cargar las reseñas.</div>`;
  }
}


// ===========================
// 🔢 Paginación helpers
// ===========================
function makePageBtn(label, page, disabled = false, active = false) {
  const btn = document.createElement("button");
  btn.className = "page-btn";
  btn.textContent = label;

  if (active) btn.classList.add("active");
  btn.disabled = disabled;

  btn.addEventListener("click", () => {
    if (lastBooksArray) {
      renderResultsLocal(lastBooksArray, page);
    } else {
      searchBooks(lastQuery, page);
    }
  });

  return btn;
}


// ===========================
// 🧹 UI: buscar / ordenar / limpiar
// ===========================
document.getElementById("searchForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  searchBooks(q, 1);
});

sortSelect.addEventListener("change", () => {
  // re-render manteniendo página
  if (lastBooksArray) {
    lastBooksArray = applySort(lastBooksArray, sortSelect.value);
    renderResultsLocal(lastBooksArray, currentPage);
  } else {
    searchBooks(lastQuery, currentPage);
  }
});

clearBtn.addEventListener("click", () => {
  document.getElementById("q").value = "";
  lastQuery = "";
  currentPage = 1;
  lastBooksArray = null;
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";
  resultsMeta.textContent = "Escribe algo y pulsa Buscar.";
  searchBooks("", 1);
});


// ===========================
// 🧰 Utils
// ===========================
function shorten(text, max) {
  const t = (text || "").trim();
  if (!t) return "—";
  return t.length > max ? t.slice(0, max - 1) + "…" : t;
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(str) {
  return escapeHtml(str).replaceAll("\n", " ").replaceAll("\r", " ");
}


// ===========================
// 🚀 Inicio
// ===========================
window.onload = async () => {
  await loadUserLoans();
  await searchBooks("", 1);
};
