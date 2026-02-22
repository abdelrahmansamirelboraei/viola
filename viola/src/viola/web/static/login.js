(function () {
  const btn = document.getElementById("btnLogin");
  const msg = document.getElementById("msg");

  function getRole() {
    const el = document.querySelector('input[name="role"]:checked');
    return el ? el.value : "user";
  }

  function setMsg(text, ok) {
    msg.textContent = text || "";
    msg.className = "msg " + (ok ? "ok" : "bad");
  }

  btn.addEventListener("click", async () => {
    setMsg("", true);

    const role = getRole();
    const username = (document.getElementById("username").value || "").trim();
    const password = (document.getElementById("password").value || "").trim();

    if (!username || !password) {
      setMsg("اكتب Username و Password", false);
      return;
    }

    btn.disabled = true;
    btn.textContent = "Logging in...";

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, username, password })
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.ok) {
        setMsg(data.error || "بيانات غير صحيحة", false);
        return;
      }

      if (data.role === "developer") {
        window.location.href = "/admin";
      } else {
        window.location.href = "/chat";
      }

    } catch (e) {
      setMsg("Server not reachable", false);
    } finally {
      btn.disabled = false;
      btn.textContent = "Login";
    }
  });
})();
