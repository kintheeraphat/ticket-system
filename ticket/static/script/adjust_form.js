document.addEventListener("DOMContentLoaded", function () {
  initAdjustTable();
  initFileUpload();
  loadDraft();
});

/* ================= TABLE (SOURCE + TARGET) ================= */
function initAdjustTable() {
  const sourceBody = document.querySelector("#sourceTable tbody");
  const targetBody = document.querySelector("#targetTable tbody");
  const addBtn = document.getElementById("addRow");

  if (!sourceBody || !targetBody || !addBtn) return;

  // เพิ่มแถว (เป็นคู่)
  addBtn.onclick = () => {
    const s = sourceBody.rows[0].cloneNode(true);
    const t = targetBody.rows[0].cloneNode(true);

    s.querySelectorAll("input").forEach((i) => (i.value = ""));
    t.querySelectorAll("input").forEach((i) => (i.value = ""));

    sourceBody.appendChild(s);
    targetBody.appendChild(t);
  };

  // ลบแถว (ลบเป็นคู่)
  targetBody.addEventListener("click", (e) => {
    if (e.target.closest(".remove-row") && targetBody.rows.length > 1) {
      const index = [...targetBody.rows].indexOf(e.target.closest("tr"));
      sourceBody.rows[index].remove();
      targetBody.rows[index].remove();
    }
  });
}

/* ================= FILE UPLOAD ================= */
window.fileUpload = { selectedFiles: [] };

function initFileUpload() {
  const preview = document.getElementById("filePreview");
  if (!preview) return;

  window.handleFiles = function (input) {
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

  async function renderFiles() {
    preview.innerHTML = "";

    for (let i = 0; i < window.fileUpload.selectedFiles.length; i++) {
      const file = window.fileUpload.selectedFiles[i];
      const url = URL.createObjectURL(file);

      const thumb = document.createElement("div");
      thumb.className = "file-thumb";
      thumb.onclick = () => openPreview(url);

      // ปุ่มลบ
      const removeBtn = document.createElement("button");
      removeBtn.className = "remove-btn";
      removeBtn.innerHTML = "×";
      removeBtn.onclick = (e) => {
        e.stopPropagation();
        window.fileUpload.selectedFiles.splice(i, 1);
        renderFiles();
      };
      thumb.appendChild(removeBtn);

      // IMAGE
      if (file.type.startsWith("image/")) {
        const img = document.createElement("img");
        img.src = url;
        thumb.appendChild(img);
      }

      // PDF
      else if (file.type === "application/pdf" && window.pdfjsLib) {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        const pdf = await pdfjsLib.getDocument(url).promise;
        const page = await pdf.getPage(1);

        const viewport = page.getViewport({ scale: 0.4 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        await page.render({ canvasContext: ctx, viewport }).promise;
        thumb.appendChild(canvas);
      }

      // filename
      const name = document.createElement("div");
      name.className = "filename";
      name.innerText = file.name;
      thumb.appendChild(name);

      preview.appendChild(thumb);
    }
  }
}

function openPreview(url) {
  const iframe = document.getElementById("previewFrame");
  iframe.src = url + "#toolbar=0&navpanes=0&scrollbar=0";
  new bootstrap.Modal(document.getElementById("fileModal")).show();
}
function saveDraft() {
  const data = {
    adj_category: document.querySelector('[name="adj_category"]').value,
    remark: document.querySelector('[name="remark"]').value,

    source: collectTable("#sourceTable"),
    target: collectTable("#targetTable"),

    files:
      window.fileUpload?.selectedFiles?.map((f) => ({
        name: f.name,
        type: f.type,
      })) || [],
  };

  localStorage.setItem("adjust_form_draft", JSON.stringify(data));
  alert("บันทึกร่างเรียบร้อยแล้ว");
}
function collectTable(selector) {
  const rows = [];
  document.querySelectorAll(`${selector} tbody tr`).forEach((tr) => {
    const row = {};
    tr.querySelectorAll("input").forEach((input) => {
      row[input.name] = input.value;
    });
    rows.push(row);
  });
  return rows;
}
function loadDraft() {
  const draft = localStorage.getItem("adjust_form_draft");
  if (!draft) return;

  const data = JSON.parse(draft);

  // ประเภท
  if (data.adj_category) {
    document.querySelector('[name="adj_category"]').value = data.adj_category;
  }

  // หมายเหตุ
  document.querySelector('[name="remark"]').value = data.remark || "";

  restoreTable("#sourceTable", data.source);
  restoreTable("#targetTable", data.target);
}
function restoreTable(selector, rows) {
  if (!rows || rows.length === 0) return;

  const tbody = document.querySelector(`${selector} tbody`);
  tbody.innerHTML = "";

  rows.forEach((rowData) => {
    const tr = document.createElement("tr");
    Object.keys(rowData).forEach((name) => {
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
document.querySelector("form").addEventListener("submit", () => {
  localStorage.removeItem("adjust_form_draft");
});
