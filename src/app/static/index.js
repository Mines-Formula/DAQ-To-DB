const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const alertContainer = document.getElementById('alertContainer');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  const isCSV = Array.from(e.dataTransfer.items)
                    .some(
                        (item) => item.type === 'text/csv' ||
                            item.type === 'application/vnd.ms-excel');

  dropZone.classList.remove('dragover', 'invalid');
  dropZone.classList.add(isCSV ? 'dragover' : 'invalid');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover', 'invalid');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover', 'invalid');

  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
  handleFiles(e.target.files);
});

function handleFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append(file.name, file);
  }

  // Clear previous alerts
  alertContainer.innerHTML = '';

  // Create a temporary endpoint for SSE upload
  // We use fetch to POST the files, then listen for SSE progress
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload", true);

  xhr.onreadystatechange = function() {
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status !== 200) {
      showAlert("Upload failed or server error.", "danger");
    }
  };

  xhr.onload = function() {
    console.log("Upload request finished.");
  };

  // Listen for SSE events via a custom EventSource
  xhr.upload.addEventListener("load", () => {
    // After upload finishes, connect to SSE stream
    const evtSource = new EventSource("/upload"); // Flask sends SSE here
    evtSource.onmessage = function(event) {
      appendStatus(event.data);
    };
    evtSource.onerror = function() {
      evtSource.close();
    };
  });

  xhr.send(formData);
}

function appendStatus(message) {
  const div = document.createElement("div");
  div.textContent = message;
  alertContainer.appendChild(div);
}

function showAlert(message, type) {
  alertContainer.innerHTML = `
    <div class="alert alert-${type} mt-3" role="alert">${message}</div>
  `;
}
