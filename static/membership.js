/* Membership sandbox client. Token kept in memory only, never persisted. */
(() => {
  "use strict";
  let token = null;
  let lastSession = null;
  const $ = (id) => document.getElementById(id);
  const show = (id, obj, ok = true) => {
    const el = $(id);
    el.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
    el.className = ok ? "ok" : "error";
  };
  async function api(path, opts = {}) {
    const res = await fetch(path, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(opts.headers || {}) },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }
  const needLogin = () => { if (!token) { show("loginMsg", "กรุณาเข้าสู่ระบบก่อน / Please log in first.", false); return false; } return true; };

  $("loginBtn").addEventListener("click", async () => {
    try {
      const data = await api("/api/v2/auth/login", { method: "POST",
        body: JSON.stringify({ username: $("username").value, password: $("password").value }) });
      token = data.token;
      $("password").value = "";
      show("loginMsg", `ยินดีต้อนรับ / Welcome, ${data.user.username}`);
    } catch (e) { show("loginMsg", `ล้มเหลว / Failed: ${e.message}`, false); }
  });
  $("plansBtn").addEventListener("click", async () => {
    try { show("plansOut", await api("/api/v2/commerce/plans")); }
    catch (e) { show("plansOut", e.message, false); }
  });
  $("subBtn").addEventListener("click", async () => {
    if (!needLogin()) return;
    try { show("subOut", await api("/api/v2/commerce/subscription")); }
    catch (e) { show("subOut", e.message, false); }
  });
  $("checkoutBtn").addEventListener("click", async () => {
    if (!needLogin()) return;
    try {
      const data = await api("/api/v2/commerce/checkout", { method: "POST",
        body: JSON.stringify({ plan_id: $("plan").value, payment_method_ref: "pm_sandbox_demo",
          idempotency_key: `idem-${Date.now()}-${Math.random().toString(16).slice(2)}` }) });
      lastSession = data.session;
      show("checkoutOut", { checkout_url: data.session.checkout_url, status: data.session.status,
        next: "กดยืนยันชำระเงิน / Press Confirm payment" });
    } catch (e) { show("checkoutOut", e.message, false); }
  });
  $("confirmBtn").addEventListener("click", async () => {
    if (!needLogin() || !lastSession) { show("checkoutOut", "สร้าง checkout ก่อน / Create checkout first.", false); return; }
    try {
      show("checkoutOut", await api("/api/v2/commerce/checkout/confirm", { method: "POST",
        body: JSON.stringify({ session_id: lastSession.session_id, plan_id: $("plan").value,
          idempotency_key: `idem-confirm-${Date.now()}` }) }));
    } catch (e) { show("checkoutOut", e.message, false); }
  });
  $("cancelBtn").addEventListener("click", async () => {
    if (!needLogin()) return;
    try { show("manageOut", await api("/api/v2/commerce/subscription/cancel", { method: "POST", body: "{}" })); }
    catch (e) { show("manageOut", e.message, false); }
  });
  $("ledgerBtn").addEventListener("click", async () => {
    if (!needLogin()) return;
    try { show("manageOut", await api("/api/v2/commerce/ledger")); }
    catch (e) { show("manageOut", e.message, false); }
  });
})();
