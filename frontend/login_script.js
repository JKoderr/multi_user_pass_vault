document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const errorMsg = document.getElementById("errorMsg");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");

  if (!form || !usernameInput || !passwordInput || !errorMsg) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    
    if (!(usernameInput instanceof HTMLInputElement) || !(passwordInput instanceof HTMLInputElement)) {
      alert("Form fields not found or incorrect.");
      return;
    }
    
    const username = usernameInput.value;
    const password = passwordInput.value;
    

    const res = await fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (res.ok) {
      localStorage.setItem("token", data.token);
      window.location.href = "dashboard.html";
    } else {
      errorMsg.textContent = data.error || "Login failed.";
    }
  });
});
