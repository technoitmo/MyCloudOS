const backend = window.MYCLOUDOS_BACKEND_URL || "http://127.0.0.1:8009";
const tokenKey = "mycloudos_access_token";

const statusBox = document.getElementById("statusBox");
const osSelect = document.getElementById("osSelect");
const instancesBody = document.getElementById("instancesBody");
const devMessages = document.getElementById("devMessages");

function getToken() {
  return localStorage.getItem(tokenKey);
}

function setToken(token) {
  localStorage.setItem(tokenKey, token);
}

function clearToken() {
  localStorage.removeItem(tokenKey);
}

function showStatus(message, level = "info") {
  if (!statusBox) return;
  statusBox.style.display = "block";
  statusBox.className = `flash flash-${level}`;
  statusBox.textContent = message;
}

async function apiCall(path, options = {}, auth = false) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (auth && getToken()) {
    headers.Authorization = `Bearer ${getToken()}`;
  }

  const response = await fetch(`${backend}${path}`, { ...options, headers });
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const detail = data.detail || `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return data;
}

async function loadOsImages() {
  const images = await apiCall("/api/cloud/os-images");
  osSelect.innerHTML = "";
  images.forEach((img) => {
    const option = document.createElement("option");
    option.value = img.id;
    option.textContent = `${img.name} (${img.family} ${img.version})`;
    osSelect.appendChild(option);
  });
}

async function loadInstances() {
  if (!getToken()) {
    instancesBody.innerHTML = "";
    return;
  }

  const instances = await apiCall("/api/cloud/instances", {}, true);
  instancesBody.innerHTML = "";
  instances.forEach((vm) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${vm.name}</td>
      <td>${vm.os_image.name}</td>
      <td><span class="status status-${vm.status}">${vm.status}</span></td>
      <td>${vm.region}</td>
      <td>${vm.public_ip || "-"}</td>
      <td>${vm.access_username || "-"}</td>
    `;
    instancesBody.appendChild(tr);
  });
}

async function loadDevMessages() {
  const messages = await apiCall("/api/dev/messages");
  devMessages.innerHTML = "";
  messages.forEach((msg) => {
    const card = document.createElement("article");
    card.className = "message-card";
    card.innerHTML = `
      <h4>${msg.subject}</h4>
      <p><strong>Destinataire:</strong> ${msg.recipient}</p>
      <pre>${msg.body}</pre>
    `;
    devMessages.appendChild(card);
  });
}

document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    await apiCall("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email: form.get("email"),
        password: form.get("password"),
      }),
    });
    showStatus("Compte cree. Verifiez votre email via code ou lien.", "success");
  } catch (err) {
    showStatus(err.message, "danger");
  }
});

document.getElementById("verifyForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    await apiCall("/api/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({
        email: form.get("email"),
        code: form.get("code"),
      }),
    });
    showStatus("Compte verifie. Vous pouvez vous connecter.", "success");
  } catch (err) {
    showStatus(err.message, "danger");
  }
});

document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    const data = await apiCall("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: form.get("email"),
        password: form.get("password"),
      }),
    });
    setToken(data.access_token);
    showStatus(`Connecte: ${data.user.email}`, "success");
    await loadInstances();
  } catch (err) {
    showStatus(err.message, "danger");
  }
});

document.getElementById("instanceForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!getToken()) {
    showStatus("Connectez-vous avant de creer une instance.", "danger");
    return;
  }

  const form = new FormData(e.target);
  try {
    await apiCall(
      "/api/cloud/instances",
      {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name"),
          os_image_id: Number(form.get("os_image_id")),
          region: form.get("region"),
          cpu_cores: Number(form.get("cpu_cores")),
          memory_gb: Number(form.get("memory_gb")),
          disk_gb: Number(form.get("disk_gb")),
        }),
      },
      true
    );
    showStatus("Instance en cours de provisioning.", "success");
    await loadInstances();
  } catch (err) {
    showStatus(err.message, "danger");
  }
});

document.getElementById("loadMessagesBtn")?.addEventListener("click", async () => {
  try {
    await loadDevMessages();
    showStatus("Messages dev rafraichis.", "info");
  } catch (err) {
    showStatus(err.message, "danger");
  }
});

document.getElementById("logoutBtn")?.addEventListener("click", () => {
  clearToken();
  instancesBody.innerHTML = "";
  showStatus("Deconnecte.", "info");
});

(async function init() {
  try {
    await loadOsImages();
    await loadDevMessages();
    if (getToken()) {
      await loadInstances();
    }
  } catch (err) {
    showStatus(err.message, "danger");
  }

  setInterval(async () => {
    try {
      await loadInstances();
    } catch {
      // Keep silent in background refresh.
    }
  }, 10000);
})();
