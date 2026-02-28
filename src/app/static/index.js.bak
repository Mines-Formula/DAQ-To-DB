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

async function handleFiles(files) {
  const formData = new FormData();

  for (const file of files) {
    formData.append(file.name, file);
  }

  try {
    const res = await fetch('/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      showAlert(data.error || 'Upload failed', 'danger');
    } else {
      showAlert(data.message, 'success');
    }
  } catch (err) {
    showAlert('Error connecting to server.', 'danger');
    console.error(err);
  }
}

function showAlert(message, type) {
  alertContainer.innerHTML = `
    <div class="alert alert-${type} mt-3" role="alert">${message}</div>
  `;
}
