// Refresh simple du dashboard pour suivre le statut de provisioning.
if (window.location.pathname === "/dashboard") {
  setInterval(() => {
    window.location.reload();
  }, 10000);
}
