const backend = window.MYCLOUDOS_BACKEND_URL || "http://127.0.0.1:8009";
const msg = document.getElementById("verifyMessage");

async function runVerification() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) {
    msg.textContent = "Token manquant.";
    return;
  }

  try {
    const response = await fetch(`${backend}/api/auth/verify?token=${encodeURIComponent(token)}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
    msg.textContent = data.message || "Verification reussie.";
  } catch (error) {
    msg.textContent = `Echec verification: ${error.message}`;
  }
}

runVerification();
