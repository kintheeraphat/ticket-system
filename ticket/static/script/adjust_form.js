document.addEventListener("DOMContentLoaded", () => {
  initAdjustTable();
  initFileUpload();
  loadDraft();
});

/* ================= TABLE (PAIR ROW) ================= */
function initAdjustTable() {
  const sourceBody = document.querySelector("#sourceTable tbody");
  const targetBody = document.querySelector("#targetTable tbody");
  const addBtn = document.getElementById("addRow");

  addBtn.onclick = () => {
    const s = sourceBody.rows[0].cloneNode(true);
    const t = targetBody.rows[0].cloneNode(true);

    s.querySelectorAll("input").forEach(i => i.value = "");
    t.querySelectorAll("input").forEach(i => i.value = "");

    sourceBody.appendChild(s);
    targetBody.appendChild(t);
  };

  targetBody.addEventListener("click", e => {
    if (e.target.closest(".remove-row") && targetBody.rows.length > 1) {
      const idx = [...targetBody.rows].indexOf(e.target.closest("tr"));
      sourceBody.rows[idx].remove();
      targetBody.rows[idx].remove();
    }
  });
}

/* ================= FILE UPLOAD ================= */
window.fileUpload = { selectedFiles: [] };

function initFileUpload() {
  window.handleFiles = input => {
    const files = Array.from(input.files);
    if (window.fileUpload.selectedFiles.length + files.length > 3) {
      alert("แนบไฟล์ได้ไม่เกิน 3 ไฟล์");
      input.value = "";
      return;
    }
    window.fileUpload.selectedFiles.push(...files);
    input.value = "";
    renderFiles();
  };
}

async function renderFiles() {
  const preview = document.getElementById("filePreview");
  preview.innerHTML = "";

  for (let i = 0; i < window.fileUpload.selectedFiles.length; i++) {
    const file = window.fileUpload.selectedFiles[i];
    const url = URL.createObjectURL(file);

    const thumb = document.createElement("div");
    thumb.className = "file-thumb";
    thumb.onclick = () => openPreview(url);

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.innerHTML = "×";
    removeBtn.onclick = e => {
      e.stopPropagation();
      window.fileUpload.selectedFiles.splice(i, 1);
      renderFiles();
    };
    thumb.appendChild(removeBtn);

    if (file.type.startsWith("image/")) {
      const img = document.createElement("img");
      img.src = url;
      thumb.appendChild(img);
    } else if (file.type === "application/pdf") {
      const canvas = document.createElement("canvas");
      const pdf = await pdfjsLib.getDocument(url).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 0.4 });
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
      thumb.appendChild(canvas);
    }

    const name = document.createElement("div");
    name.className = "filename";
    name.innerText = file.name;
    thumb.appendChild(name);

    preview.appendChild(thumb);
  }
}

function openPreview(url) {
  document.getElementById("previewFrame").src = url;
  new bootstrap.Modal(document.getElementById("fileModal")).show();
}

/* ================= DRAFT ================= */
function saveDraft() {
  const data = {
    adj_category: document.querySelector('[name="adj_category"]').value,
    remark: document.querySelector('[name="remark"]').value,
    source: collectTable("#sourceTable"),
    target: collectTable("#targetTable")
  };
  localStorage.setItem("adjust_form_draft", JSON.stringify(data));
  alert("บันทึกร่างเรียบร้อย");
}

function loadDraft() {
  const draft = localStorage.getItem("adjust_form_draft");
  if (!draft) return;

  const data = JSON.parse(draft);
  document.querySelector('[name="adj_category"]').value = data.adj_category || "";
  document.querySelector('[name="remark"]').value = data.remark || "";

  restoreTable("#sourceTable", data.source);
  restoreTable("#targetTable", data.target);
}

function collectTable(selector) {
  const rows = [];
  document.querySelectorAll(`${selector} tbody tr`).forEach(tr => {
    const row = {};
    tr.querySelectorAll("input").forEach(i => row[i.name] = i.value);
    rows.push(row);
  });
  return rows;
}

function restoreTable(selector, rows) {
  if (!rows || rows.length === 0) return;
  const tbody = document.querySelector(`${selector} tbody`);
  tbody.innerHTML = "";

  rows.forEach(rowData => {
    const tr = document.createElement("tr");
    Object.keys(rowData).forEach(name => {
      const td = document.createElement("td");
      const input = document.createElement("input");
      input.className = "form-control";
      input.name = name;
      input.value = rowData[name];
      td.appendChild(input);
      tr.appendChild(td);
    });

    if (selector === "#targetTable") {
      const td = document.createElement("td");
      td.innerHTML = `<button type="button" class="btn btn-outline-danger btn-sm remove-row">&times;</button>`;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  });
}

document.querySelector("#adjustForm").addEventListener("submit", () => {
  localStorage.removeItem("adjust_form_draft");
});
