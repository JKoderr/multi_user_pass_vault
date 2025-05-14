document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("passGenForm");
  const errorMsg = document.getElementById("errorMsg");
  const lengthInput = document.getElementById("length");
  const serviceInput = document.getElementById("service");
  const passwordList = document.getElementById("passwordList");


  if (!form || !errorMsg || !lengthInput || !serviceInput || !passwordList) {
    console.error("Brakuje któregoś z elementów formularza.");
    return;
  }
  

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    if (!(lengthInput instanceof HTMLInputElement) || !(serviceInput instanceof HTMLInputElement)) {
      alert("Form fields not found or incorrect.");
      return;
    }

    const length = parseInt(lengthInput.value);
    const service = serviceInput.value;
    const token = localStorage.getItem("token");

    if (!token) {
      errorMsg.textContent = "You are not logged in!";
      window.location.href = "login.html";
    }

    try {
      const res = await fetch("http://127.0.0.1:5000/generate-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ length, service })
      });

      const data = await res.json();

      if (data.error === "Expired") {
        localStorage.removeItem("token");
        window.location.replace("http://127.0.0.1:5500/backend_vault/multi_user_pass_vault/frontend/login.html");
        return;
      }

      if (res.ok) {
        alert(`Your password: ${data.password}`);
        fetchPasswords(); //refresh after adding new pass
      } else {
        errorMsg.textContent = data.error || "Error occurred.";
      }
    } catch (err) {
      errorMsg.textContent = "Request failed.";
    }
  });

  async function fetchPasswords() {
    const token = localStorage.getItem("token");
    if (!token) return;

    if (!passwordList){
        console.error("passwordList not found");
        return;
      }

    try {
      const res = await fetch("http://127.0.0.1:5000/get-passwords", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      const data = await res.json();

      if (data.error === "Expired") {
        localStorage.removeItem("token");
        window.location.replace("http://127.0.0.1:5500/backend_vault/multi_user_pass_vault/frontend/login.html");
        return;
        }

      
      if (!Array.isArray(data["Your data"])) {
        passwordList.textContent = "No passwords found or error occurred.";
        return;
      }

      passwordList.innerHTML = "";
      data["Your data"].forEach((entry) => {
        const item = document.createElement("div");

      const text = document.createElement("span");
      text.textContent = `${entry.service}: ${entry.password} (${entry.timestamp})`;

      const delBtn = document.createElement("button");
      delBtn.textContent = "Delete the password";
      delBtn.style.marginLeft = "10px";

      delBtn.addEventListener("click", async () => {
        const token = localStorage.getItem("token");
        if (!token) return;

        const confirmed = confirm("Are you sure you want to delete this password?");
        if (!confirmed) return;

        try {
          const res = await fetch(`http://127.0.0.1:5000/delete-password/${entry.id}`, {
            method: "DELETE",
            headers: {
              "Authorization": `Bearer ${token}`
            }
          });

          const result = await res.json();

          if (res.ok) {
            alert(result.message);
            fetchPasswords(); // Odśwież hasła
          } else {
            alert(result.error || "Error deleting password.");
          }
        } catch {
          alert("Failed to delete password.");
        }
      });

      item.appendChild(text);
      item.appendChild(delBtn);
      passwordList.appendChild(item);
    });
    } catch {
      passwordList.textContent = "Failed to load passwords.";
    }
  }

  const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "login.html";
  });
}


  fetchPasswords();
});
