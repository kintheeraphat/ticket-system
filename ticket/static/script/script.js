/* =====================================================
   GLOBAL STATE
===================================================== */
window.fileUpload = {
  selectedFiles: []
};

/* =====================================================
   DOM READY
===================================================== */
document.addEventListener("DOMContentLoaded", function () {
  initChart();
  initSidebar();
  initDynamicInputs();
  initLocalStorageForm();
  initDownloadButton();
  initFileUpload();
  initAdjustTable();
});

/* =====================================================
   DASHBOARD CHART
===================================================== */
function initChart() {
  const chartCanvas = document.getElementById("ticketChart");
  if (!chartCanvas || !window.Chart) return;

  const ctx = chartCanvas.getContext("2d");
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Network", "Hardware", "Software", "Access"],
      datasets: [{
        data: [45, 32, 18, 10],
        backgroundColor: ["#2563eb", "#f59e0b", "#10b981", "#64748b"],
        hoverOffset: 15,
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
            font: { size: 12, family: "'Inter', sans-serif" },
          },
        },
      },
      cutout: "70%",
    }
  });
}

/* =====================================================
   SIDEBAR (MOBILE)
===================================================== */
function initSidebar() {
  const toggleBtn = document.getElementById("mobile-sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");

  if (!toggleBtn || !sidebar || !overlay) return;

  toggleBtn.addEventListener("click", function () {
    sidebar.classList.toggle("show");
    overlay.style.display = sidebar.classList.contains("show")
      ? "block"
      : "none";
  });

  overlay.addEventListener("click", function () {
    sidebar.classList.remove("show");
    overlay.style.display = "none";
  });
}

/* =====================================================
   ADD INPUT (NAME / MODULE)
===================================================== */
function initDynamicInputs() {
  document.querySelectorAll(".add-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const wrapperSelector = btn.getAttribute("data-target");
      const wrapper = document.querySelector(wrapperSelector);
      if (!wrapper) return;

      if (wrapper.classList.contains("names-wrapper")) {
        wrapper.appendChild(createSimpleInput("name_en[]", "ชื่อ-นามสกุล"));
      }

      if (wrapper.classList.contains("modules-wrapper")) {
        wrapper.appendChild(
          createSimpleInput(
            "erp_module[]",
            "รายละเอียดที่ต้องการ เช่น ใช้โปรไฟล์อะไร ต้องการเพิ่มอะไร"
          )
        );
      }
    });
  });
}

function createSimpleInput(name, placeholder) {
  const input = document.createElement("input");
  input.type = "text";
  input.name = name;
  input.placeholder = placeholder;
  input.className = "form-control mb-1";
  return input;
}

/* =====================================================
   LOCAL STORAGE (ERP FORM)
===================================================== */
function initLocalStorageForm() {
  const nameContainer = document.getElementById("nameFields");
  const moduleContainer = document.getElementById("moduleFields");
  const remarkField = document.querySelector('textarea[name="remark"]');
  const labelName = document.getElementById("labelName");

  if (!nameContainer || !moduleContainer) return;

  function createRow(name, placeholder, value = "") {
    const div = document.createElement("div");
    div.className = "d-flex mb-2";
    div.innerHTML = `
      <input class="form-control me-2" name="${name}" placeholder="${placeholder}" value="${value}">
      <button type="button" class="btn btn-danger btn-sm remove-btn">ลบ</button>
    `;
    return div;
  }

  function saveToLocal() {
    const requestType = document.querySelector('input[name="request_type"]:checked')?.value;
    localStorage.setItem("erp_form_data", JSON.stringify({
      request_type: requestType,
      names: [...document.querySelectorAll('input[name="name_en[]"]')].map(i => i.value),
      modules: [...document.querySelectorAll('input[name="erp_module[]"]')].map(i => i.value),
      remark: remarkField?.value || ""
    }));
  }

  function loadFromLocal() {
    const data = JSON.parse(localStorage.getItem("erp_form_data"));
    if (!data) return;

    if (remarkField) remarkField.value = data.remark || "";

    if (data.names?.length) {
      nameContainer.innerHTML = "";
      data.names.forEach((v, i) => {
        const row = createRow("name_en[]", "ชื่อ-นามสกุล", v);
        if (i === 0) row.querySelector(".remove-btn").style.visibility = "hidden";
        nameContainer.appendChild(row);
      });
    }

    if (data.modules?.length) {
      moduleContainer.innerHTML = "";
      data.modules.forEach((v, i) => {
        const row = createRow(
          "erp_module[]",
          "รายละเอียดที่ต้องการ เช่น ใช้โปรไฟล์อะไร ต้องการเพิ่มอะไร",
          v
        );
        if (i === 0) row.querySelector(".remove-btn").style.visibility = "hidden";
        moduleContainer.appendChild(row);
      });
    }

    if (labelName && data.request_type) {
      labelName.innerText =
        data.request_type === "adjust_perm"
          ? "ชื่อ-นามสกุล / User ERP ที่ต้องการปรับสิทธิ์"
          : "ชื่อ-นามสกุล สำหรับเปิด User ใหม่";
    }
  }

  loadFromLocal();
  document.addEventListener("input", saveToLocal);

  document.addEventListener("click", e => {
    if (e.target.classList.contains("remove-btn")) {
      e.target.closest(".d-flex").remove();
      saveToLocal();
    }
  });
}

/* =====================================================
   DOWNLOAD BUTTON
===================================================== */
function initDownloadButton() {
  const downloadBtn = document.getElementById("downloadBtn");
  if (!downloadBtn) return;

  document.querySelectorAll('input[name="request_type"]').forEach(radio => {
    radio.addEventListener("change", e => {
      if (e.target.value === "adjust_perm") {
        downloadBtn.href = "/static/docs/IT-ERP-001_V1.pdf";
        downloadBtn.innerHTML = '<i class="fas fa-file-download me-1"></i> ดาวน์โหลดแบบฟอร์มปรับสิทธิ์';
      } else {
        downloadBtn.href = "/static/docs/IT-ERP-004_V1.pdf";
        downloadBtn.innerHTML = '<i class="fas fa-file-download me-1"></i> ดาวน์โหลดแบบฟอร์มเปิด User';
      }
    });
  });
}

/* =====================================================
   FILE UPLOAD + PREVIEW (MAX 3 FILES)
===================================================== */
function initFileUpload() {
  const preview = document.getElementById("filePreview");
  if (!preview) return;

  window.fileUpload.selectedFiles = [];

  window.handleFiles = function (input) {
    if (!input.files) return;

    const newFiles = Array.from(input.files);

    // จำกัดไม่เกิน 3 ไฟล์
    if (window.fileUpload.selectedFiles.length + newFiles.length > 3) {
      alert("แนบไฟล์ได้ไม่เกิน 3 ไฟล์");
      input.value = "";
      return;
    }

    window.fileUpload.selectedFiles.push(...newFiles);
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
      removeBtn.innerHTML = "&times;";
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
        const pdf = await pdfjsLib.getDocument(url).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 0.4 });

        canvas.width = viewport.width;
        canvas.height = viewport.height;

        await page.render({
          canvasContext: canvas.getContext("2d"),
          viewport,
        }).promise;

        thumb.appendChild(canvas);
      }

      // ชื่อไฟล์
      const name = document.createElement("div");
      name.className = "filename";
      name.innerText = file.name;
      thumb.appendChild(name);

      preview.appendChild(thumb);
    }
  }
}


/* =====================================================
   FILE MODAL PREVIEW
===================================================== */
function openPreview(url) {
  const iframe = document.getElementById("previewFrame");
  if (!iframe) return;

  iframe.src = url + "#toolbar=0&navpanes=0&scrollbar=0";
  new bootstrap.Modal(document.getElementById("fileModal")).show();
}

/* =====================================================
   ADJUST TABLE (ADD / REMOVE ROW)
===================================================== */
function initAdjustTable() {
  const tableBody = document.querySelector("#adjustTable tbody");
  const addBtn = document.getElementById("addRow");
  if (!tableBody || !addBtn) return;

  addBtn.addEventListener("click", function () {
    const row = tableBody.rows[0].cloneNode(true);
    row.querySelectorAll("input").forEach(i => i.value = "");
    tableBody.appendChild(row);
  });

  tableBody.addEventListener("click", function (e) {
    if (e.target.closest(".remove-row") && tableBody.rows.length > 1) {
      e.target.closest("tr").remove();
    }
  });
}