const output = document.querySelector("#output");
const scanBtn = document.querySelector("#scanBtn");
const emailBtn = document.querySelector("#emailBtn");
const clearBtn = document.querySelector("#clearBtn");

function stamp(title, payload) {
  const time = new Date().toLocaleTimeString();
  const text = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  output.textContent = `[${time}] ${title}\n\n${text}\n\n${output.textContent === "Ready." ? "" : output.textContent}`;
}

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

scanBtn.addEventListener("click", async () => {
  const target = document.querySelector("#target").value.trim();
  const preset = document.querySelector("#preset").value;
  scanBtn.disabled = true;
  scanBtn.textContent = "Scanning...";
  try {
    const result = await postJSON("/api/nmap", { target, preset });
    if (result.stdout) {
      stamp("Nmap result", result.stdout);
    } else {
      stamp("Nmap result", result);
    }
  } catch (error) {
    stamp("Nmap error", error.message);
  } finally {
    scanBtn.disabled = false;
    scanBtn.textContent = "Run scan";
  }
});

emailBtn.addEventListener("click", async () => {
  const email = document.querySelector("#email").value.trim();
  emailBtn.disabled = true;
  emailBtn.textContent = "Checking...";
  try {
    const result = await postJSON("/api/email", { email });
    stamp("Email check", result);
  } catch (error) {
    stamp("Email error", error.message);
  } finally {
    emailBtn.disabled = false;
    emailBtn.textContent = "Check email";
  }
});

clearBtn.addEventListener("click", () => {
  output.textContent = "Ready.";
});
