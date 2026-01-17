let adminAuth = null;

const statusEl = document.getElementById("status");
const adminForm = document.getElementById("adminForm");

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

async function refreshBooks() {
  const list = document.getElementById("bookList");
  list.textContent = "Cargando…";
  const res = await fetch("/admin/books", { headers: { Authorization: adminAuth }});
  if (!res.ok) {
    list.textContent = "No se pudieron cargar los libros.";
    return;
  }
  const data = await res.json();
  if (!data.length) {
    list.textContent = "No hay libros añadidos.";
    return;
  }

  list.innerHTML = data.map(b => `
    <div style="padding:10px;border:1px solid rgba(255,255,255,.08);border-radius:14px;margin-bottom:8px;">
      <b>${b.title}</b> — <span style="opacity:.8">${b.author || "Desconocido"}</span>
      <div style="opacity:.65;font-size:.9rem;margin-top:4px;">ID: ${b.id} · ${new Date(b.created_at).toLocaleString()}</div>
      <button class="btn danger" onclick="deleteBook(${b.id})" style="margin-top:8px;">Eliminar</button>
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

adminForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const u = document.getElementById("adminUser").value.trim();
  const p = document.getElementById("adminPass").value.trim();
  adminAuth = buildAuth(u, p);

  const ok = await ping();
  if (!ok) {
    setStatus("Credenciales incorrectas ❌", false);
    adminAuth = null;
    return;
  }

  setStatus("Login admin correcto ✅");
  refreshBooks();
});

document.getElementById("deleteReviewBtn").addEventListener("click", async () => {
  if (!adminAuth) return setStatus("Primero haz login admin.", false);

  const id = document.getElementById("reviewId").value.trim();
  if (!id) return setStatus("Pon un review_id.", false);

  const res = await fetch(`/admin/reviews/${id}`, {
    method: "DELETE",
    headers: { Authorization: adminAuth }
  });

  if (!res.ok) return setStatus("No se pudo eliminar la reseña.", false);
  setStatus("Reseña eliminada ✅");
});

document.getElementById("deleteUserBtn").addEventListener("click", async () => {
  if (!adminAuth) return setStatus("Primero haz login admin.", false);

  const u = document.getElementById("delUsername").value.trim();
  if (!u) return setStatus("Pon un username.", false);

  const res = await fetch(`/admin/users/${u}`, {
    method: "DELETE",
    headers: { Authorization: adminAuth }
  });

  if (!res.ok) return setStatus("No se pudo eliminar el usuario.", false);
  setStatus("Usuario eliminado ✅");
});

document.getElementById("addBookBtn").addEventListener("click", async () => {
  if (!adminAuth) return setStatus("Primero haz login admin.", false);

  const payload = {
    title: document.getElementById("bookTitle").value.trim(),
    author: document.getElementById("bookAuthor").value.trim(),
    language: document.getElementById("bookLang").value.trim(),
    text_url: document.getElementById("bookTextUrl").value.trim(),
    cover_url: document.getElementById("bookCoverUrl").value.trim(),
  };

  if (!payload.title) return setStatus("El título es obligatorio.", false);

  const res = await fetch("/admin/books", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: adminAuth
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) return setStatus("No se pudo añadir el libro.", false);

  setStatus("Libro añadido ✅");
  refreshBooks();
});
