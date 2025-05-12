document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
  
    const length = document.getElementById("length").value;
    const service = document.getElementById("service").value;
    const token = localStorage.getItem("token");
  
    if (!token) {
      document.getElementById("errorMsg").textContent = "You are not logged in!";
      return;
    }
  
    try {
      const res = await fetch("http://127.0.0.1:5000/generate-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ length: parseInt(length), service })
      });
  
      const data = await res.json();
  
      if (res.ok) {
        alert(`Your password: ${data.password}`);
      } else {
        document.getElementById("errorMsg").textContent = data.error || "Error occurred.";
      }
  
    } catch (err) {
      document.getElementById("errorMsg").textContent = "Request failed.";
    }
  });
  