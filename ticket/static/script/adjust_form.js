let selectedFiles = [];

function handleFiles(input) {

    const preview = document.getElementById("filePreview");
    preview.innerHTML = "";

    selectedFiles = Array.from(input.files);

    if (selectedFiles.length > 3) {
        alert("อัปโหลดได้ไม่เกิน 3 ไฟล์");
        input.value = "";
        selectedFiles = [];
        return;
    }

    selectedFiles.forEach((file, index) => {

        const reader = new FileReader();

        reader.onload = function (e) {

            const wrapper = document.createElement("div");
            wrapper.style.width = "150px";
            wrapper.className = "text-center";

            let content = "";

            if (file.type.startsWith("image/")) {
                content = `
                    <img src="${e.target.result}"
                         class="img-fluid rounded shadow-sm mb-2"
                         style="height:110px;object-fit:cover;cursor:pointer;"
                         onclick="previewFile('${e.target.result}', 'image')">
                `;
            } else if (file.type.includes("pdf")) {
                content = `
                    <div style="height:110px;display:flex;
                                align-items:center;
                                justify-content:center;
                                cursor:pointer;"
                         onclick="previewFile('${e.target.result}', 'pdf')">
                        <i class="fas fa-file-pdf text-danger fs-1"></i>
                    </div>
                `;
            } else {
                content = `
                    <div style="height:110px;display:flex;
                                align-items:center;
                                justify-content:center;">
                        <i class="fas fa-file text-secondary fs-1"></i>
                    </div>
                `;
            }

            wrapper.innerHTML = `
                ${content}
                <div class="small text-truncate">${file.name}</div>
            `;

            preview.appendChild(wrapper);
        };

        reader.readAsDataURL(file);
    });
}


/* ================= POPUP ================= */
function previewFile(src, type) {

    const frame = document.getElementById("previewFrame");
    frame.src = src;

    new bootstrap.Modal(
        document.getElementById("fileModal")
    ).show();
}
