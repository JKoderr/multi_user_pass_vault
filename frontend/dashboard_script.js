document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("passGenForm");
    const errorMsg = document.getElementById("errorMsg");
    const lengthInput = document.getElementById("length");
    const serviceInput = document.getElementById("service");
  
    if (!form || !errorMsg || !lengthInput || !serviceInput) return;
  
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
  
      const lengthInput = document.getElementById("length");
      const serviceInput = document.getElementById("service");

        if (
        !(lengthInput instanceof HTMLInputElement) ||
        !(serviceInput instanceof HTMLInputElement)
        ) {
        console.error("Elementy formularza nie są inputami.");
        return;
        }

        const length = parseInt(lengthInput.value);
        const service = serviceInput.value;

      const token = localStorage.getItem("token");
  
      if (!token) {
        errorMsg.textContent = "You are not logged in!";
        return;
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
  
        if (res.ok) {
          alert(`Your password: ${data.password}`);
        } else {
          errorMsg.textContent = data.error || "Error occurred.";
        }
  
      } catch (err) {
        errorMsg.textContent = "Request failed.";
      }
    });
  });
  