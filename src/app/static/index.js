const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const alertContainer = document.getElementById('alertContainer');

let pollIntervalId = null;

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.remove('invalid');
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover', 'invalid');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover', 'invalid');

  if (!e.dataTransfer.files || e.dataTransfer.files.length === 0) {
    showAlert('No files dropped.', 'warning');
    return;
  }

  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
  if (!e.target.files || e.target.files.length === 0) {
    return;
  }
  handleFiles(e.target.files);
});

function handleFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    // Backend just loops over request.files.values() so key name doesn't matter
    formData.append(file.name, file);
  }

  // Clear previous alerts
  alertContainer.innerHTML = '';

  // Stop any previous polling loop
  if (pollIntervalId !== null) {
    clearInterval(pollIntervalId);
    pollIntervalId = null;
  }

  showAlert('Uploading file(s) and starting conversion…', 'info');

  fetch('/upload', {
    method: 'POST',
    body: formData,
  })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Upload failed or server error.');
        }
        return response.json();
      })
      .then((data) => {
        const taskName = data.name;
        if (!taskName) {
          throw new Error('Server did not return a task name.');
        }

        // Start polling /progress with this task name
        startPolling(taskName);
      })
      .catch((error) => {
        console.error(error);
        showAlert(error.message || 'Upload failed or server error.', 'danger');
      });
}

function startPolling(taskName) {
  if (pollIntervalId !== null) {
    clearInterval(pollIntervalId);
  }

  updateProgressDisplay(0);

  pollIntervalId = setInterval(async () => {
    try {
      const response =
          await fetch(`/progress?name=${encodeURIComponent(taskName)}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Task not found on server.');
        }
        throw new Error('Failed to get progress from server.');
      }

      const data = await response.json();

      if (data.exception.present) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
        return showAlert(`Error: ${data.exception.type}`, 'danger');
      }

      const progress = typeof data.progress === 'number' ? data.progress : 0;

      updateProgressDisplay(progress);

      if (progress >= 100) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
        showAlert('Upload and processing complete!', 'success');
        loadFiles();
      }
    } catch (err) {
      console.error(err);
      clearInterval(pollIntervalId);
      pollIntervalId = null;
      showAlert('Error while checking progress.', 'danger');
    }
  }, 500);
}

function updateProgressDisplay(percent) {
  const clamped = Math.min(Math.max(percent, 0), 100);
  showAlert(`Processing: ${clamped}%`, 'info');
}

function showAlert(message, type) {
  alertContainer.innerHTML = `
    <div class='alert alert-${type} mt-3' role='alert'>${message}</div>
  `;
}

async function loadFiles() {
  const list = document.getElementById('fileList');
  list.innerHTML = '';

  try {
    const res = await fetch('/files');
    const files = await res.json();

    if (files.length === 0) {
      list.innerHTML =
          `<li class="list-group-item text-muted">No files found</li>`;
      return;
    }

    for (const file of files) {
      const li = document.createElement('li');
      li.className =
          'list-group-item d-flex justify-content-between align-items-center';

      const nameSpan = document.createElement('span');
      nameSpan.textContent = file;
      nameSpan.className = 'me-2 text-truncate';
      nameSpan.style.maxWidth = '240px';

      const downloadA = document.createElement('a');
      downloadA.className = 'btn btn-sm btn-outline-primary';
      downloadA.textContent = 'Download';
      downloadA.href = `/files/download/${encodeURIComponent(file)}`;
      downloadA.setAttribute('download', '');

      li.appendChild(nameSpan);
      li.appendChild(downloadA);
      list.appendChild(li);
    }

  } catch (err) {
    list.innerHTML =
        `<li class="list-group-item text-danger">Failed to load files</li>`;
  }
}

loadFiles();
