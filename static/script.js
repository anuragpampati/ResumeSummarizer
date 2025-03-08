document.getElementById("uploadForm").addEventListener("submit", async function(e) {
    e.preventDefault();
  
    const fileInput = document.getElementById("resumeFile");
    if (!fileInput.files.length) {
      alert("Please select a file first.");
      return;
    }
  
    const formData = new FormData();
    formData.append("resume", fileInput.files[0]);
  
    try {
      const response = await fetch("http://127.0.0.1:5000/summarize", {
        method: "POST",
        body: formData
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        document.getElementById("summaryContainer").innerHTML = 
          `<p style="color: red;">Error: ${errorData.error || "Something went wrong."}</p>`;
        return;
      }
  
      const data = await response.json();
      document.getElementById("summaryContainer").innerHTML = `
        <h2>Summary:</h2>
        <p>${data.summary}</p>
      `;
    } catch (error) {
      document.getElementById("summaryContainer").innerHTML = 
        `<p style="color: red;">Error: ${error.message}</p>`;
    }
  });
  