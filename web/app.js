// ===========================
// 📚 Alejandría - app.js
// ===========================

const username = localStorage.getItem("username");
const usernameSpan = document.getElementById("usernameSpan");
const resultsDiv = document.getElementById("results");
const paginationDiv = document.getElementById("pagination");
const loansDiv = document.getElementById("userLoans");
const messageDiv = document.getElementById("message");
const noLoansMsg = document.getElementById("noLoansMsg");

let currentPage = 1;
const pageSize = 5;

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
// 💬 Utilidad de mensajes
// ===========================
function showMessage(text, error = false) {
  messageDiv.textContent = text;
  messageDiv.className = error ? "message error" : "message success";
  setTimeout(() => {
    messageDiv.textContent = "";
  }, 3000);
}

// ===========================
// 📚 Préstamos
// ===========================
async function loadUserLoans() {
  loansDiv.innerHTML = "";
  try {
    const res = await fetch(`/loans/?username=${encodeURIComponent(username)}`);
    const data = await res.json();
    const loans = data.loans || [];

    if (!loans.length) {
      noLoansMsg.style.display = "block";
      return;
    }

    noLoansMsg.style.display = "none";
    loans.forEach((loan) => {
      const item = document.createElement("div");
      item.classList.add("loan-item");
      item.innerHTML = `
        <strong>${loan.title}</strong>
        <em>${loan.author}</em>
        <small>📅 ${new Date(loan.created_at).toLocaleDateString()}</small>
        <div>
          <button class="open-visor-btn" data-id="${loan.guten_id}" data-title="${loan.title}">
            📖 Leer
          </button>
          <button class="return-btn" data-id="${loan.guten_id}">
            ↩ Devolver
          </button>
        </div>
      `;
      loansDiv.appendChild(item);
    });

    // Botón para abrir visor
    document.querySelectorAll(".open-visor-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const id = e.target.dataset.id;
        const title = e.target.dataset.title;
        window.location.href = `/static/visor.html?id=${id}&title=${encodeURIComponent(title)}`;
      });
    });

    // Botón para devolver libro
    document.querySelectorAll(".return-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id;
        const res = await fetch(`/loans/${username}/${id}`, { method: "DELETE" });
        if (!res.ok) return showMessage("❌ Error al devolver el libro.", true);
        showMessage("↩ Libro devuelto correctamente.");
        loadUserLoans();
      });
    });
  } catch (err) {
    console.error("Error cargando préstamos:", err);
  }
}


// ===========================
// 🔍 Buscar libros
// ===========================
async function searchBooks(query = "", page = 1) {
  resultsDiv.innerHTML = "<p>Buscando...</p>";
  try {
    const res = await fetch(`/catalog/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    const books = data.results || data;
    renderResults(books, page);
  } catch {
    resultsDiv.innerHTML = "<p>⚠️ Error al buscar libros.</p>";
  }
}

function renderResults(books, page = 1) {
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";

  if (!books.length) {
    resultsDiv.innerHTML = "<p>No se encontraron resultados.</p>";
    return;
  }

  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const pageBooks = books.slice(start, end);

  pageBooks.forEach((book) => {
    const div = document.createElement("div");
    div.className = "book-card";
    div.innerHTML = `
      <h3>${book.title}</h3>
      <p><em>${book.author}</em></p>
      <p>🌐 ${book.language || "?"}</p>
      <div class="actions">
        <button class="loan-btn" data-id="${book.guten_id}" data-title="${book.title}" data-author="${book.author}">📚 Tomar en préstamo</button>
        <button class="review-btn" data-id="${book.guten_id}" data-title="${book.title}">📝 Reseñar</button>
      </div>
      <div class="reviews-container" id="reviews-${book.guten_id}"></div>
    `;
    resultsDiv.appendChild(div);
    loadReviews(book.guten_id);
  });

  // Paginación
  const totalPages = Math.ceil(books.length / pageSize);
  if (totalPages > 1) {
    const prev = document.createElement("button");
    prev.textContent = "⬅ Anterior";
    prev.disabled = page === 1;
    prev.onclick = () => renderResults(books, page - 1);

    const next = document.createElement("button");
    next.textContent = "Siguiente ➡";
    next.disabled = page === totalPages;
    next.onclick = () => renderResults(books, page + 1);

    paginationDiv.append(prev);
    paginationDiv.append(` Página ${page} de ${totalPages} `);
    paginationDiv.append(next);
  }

  // Acciones
  document.querySelectorAll(".loan-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      const title = e.target.dataset.title;
      const author = e.target.dataset.author;

      const res = await fetch("/loans/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, guten_id: id, title, author }),
      });
      if (res.status === 409) return showMessage("⚠️ Ya tienes este libro en préstamo.");
      if (!res.ok) return showMessage("❌ Error al tomar el préstamo.", true);
      showMessage(`✅ "${title}" añadido a tus préstamos.`);
      loadUserLoans();
    });
  });

  document.querySelectorAll(".review-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const id = e.target.dataset.id;
      const title = e.target.dataset.title;
      writeReview(id, title);
    });
  });
}

// ===========================
// 📝 Reseñas
// ===========================
async function writeReview(guten_id, title) {
  const rating = prompt(`Puntuación (1–5 estrellas) para "${title}":`);
  if (!rating || isNaN(rating) || rating < 1 || rating > 5) return;
  const text = prompt("Escribe tu reseña:") || "";

  const res = await fetch(`/reviews/${guten_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, rating: parseInt(rating), text }),
  });
  if (!res.ok) return showMessage("❌ Error al enviar reseña.", true);
  showMessage("📝 Reseña enviada.");
  loadReviews(guten_id);
}

async function loadReviews(guten_id) {
  const container = document.getElementById(`reviews-${guten_id}`);
  try {
    const res = await fetch(`/reviews/${guten_id}`);
    if (!res.ok) throw new Error("Error al cargar reseñas");
    const data = await res.json();
    const reviews = data || [];
    container.innerHTML = reviews.length
      ? reviews
          .map(
            (r) => `
          <div class="review-item">
            <p class="review-meta">⭐${r.rating} — ${r.username} (${new Date(r.created_at).toLocaleDateString()})</p>
            <p class="review-text">${r.text}</p>
          </div>`
          )
          .join("")
      : "<p class='no-reviews'>Sin reseñas aún.</p>";
  } catch {
    container.innerHTML = "<p class='no-reviews'>No se pudieron cargar las reseñas.</p>";
  }
}

// ===========================
// 🚀 Inicio
// ===========================
document.getElementById("searchForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  searchBooks(q);
});

window.onload = () => {
  loadUserLoans();
  searchBooks();
};
