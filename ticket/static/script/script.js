// TestChartหน้าDashboard
document.addEventListener('DOMContentLoaded', function () {
    const chartCanvas = document.getElementById('ticketChart');
    
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Network', 'Hardware', 'Software', 'Access'],
                datasets: [{
                    data: [45, 32, 18, 10], 
                    backgroundColor: [
                        '#2563eb', 
                        '#f59e0b', 
                        '#10b981', 
                        '#64748b'  
                    ],
                    hoverOffset: 15,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12, family: "'Inter', sans-serif" }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        overlay.style.display = sidebar.classList.contains('show') ? 'block' : 'none';
    });

    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.style.display = 'none';
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // เลือกทุกปุ่ม add-btn
    document.querySelectorAll('.add-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const wrapperSelector = btn.getAttribute('data-target');
            const wrapper = document.querySelector(wrapperSelector);

            // ถ้าเป็น names-wrapper
            if (wrapper.classList.contains('names-wrapper')) {
                const input = document.createElement('input');
                input.type = 'text';
                input.name = 'name_en[]';
                input.placeholder = 'เช่น John Doe';
                input.classList.add('form-control', 'mb-1');
                wrapper.appendChild(input);
            }

            // ถ้าเป็น modules-wrapper
            if (wrapper.classList.contains('modules-wrapper')) {
                const input = document.createElement('input');
                input.type = 'text';
                input.name = 'erp_module[]';
                input.placeholder = 'เช่น Sales, Accounting';
                input.classList.add('form-control', 'mb-1');
                wrapper.appendChild(input);
            }
        });
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const nameContainer = document.getElementById("nameFields");
    const moduleContainer = document.getElementById("moduleFields");
    const remarkField = document.querySelector('textarea[name="remark"]');
    const labelName = document.getElementById("labelName");

    function createNewRow(nameAttr, placeholder, value = "") {
        const div = document.createElement("div");
        div.className = "d-flex mb-2 animate-fade-in";
        div.innerHTML = `
            <input type="text" name="${nameAttr}" class="form-control me-2" placeholder="${placeholder}" value="${value}">
            <button type="button" class="btn btn-danger btn-sm remove-btn">ลบ</button>
        `;
        return div;
    }

    // --- บันทึกลง LocalStorage ---
    function saveToLocal() {
        const requestType = document.querySelector('input[name="request_type"]:checked').value;
        const data = {
            request_type: requestType,
            names: Array.from(document.querySelectorAll('input[name="name_en[]"]')).map(input => input.value),
            modules: Array.from(document.querySelectorAll('input[name="erp_module[]"]')).map(input => input.value),
            remark: remarkField ? remarkField.value : ""
        };
        localStorage.setItem('erp_form_data', JSON.stringify(data));
    }

    // --- ดึงข้อมูลกลับมาแสดง ---
    function loadFromLocal() {
        const savedData = JSON.parse(localStorage.getItem('erp_form_data'));
        if (!savedData) return;

        // โหลดประเภทคำร้อง
        if (savedData.request_type) {
            const radio = document.querySelector(`input[name="request_type"][value="${savedData.request_type}"]`);
            if (radio) {
                radio.checked = true;
                updateUI(savedData.request_type);
            }
        }

        if (remarkField) remarkField.value = savedData.remark || "";

        // โหลด Names
        if (savedData.names && savedData.names.length > 0) {
            nameContainer.innerHTML = "";
            savedData.names.forEach((val, index) => {
                const row = createNewRow("name_en[]", "ชื่อ-นามสกุล", val);
                if (index === 0) row.querySelector('.remove-btn').style.visibility = 'hidden';
                nameContainer.appendChild(row);
            });
        }

        // โหลด Modules
        if (savedData.modules && savedData.modules.length > 0) {
            moduleContainer.innerHTML = "";
            savedData.modules.forEach((val, index) => {
                const row = createNewRow("erp_module[]", "รายละเอียดที่ต้องการ เช่น ใช้โปรไฟล์อะไร ต้องการเพิ่มอะไร", val);
                if (index === 0) row.querySelector('.remove-btn').style.visibility = 'hidden';
                moduleContainer.appendChild(row);
            });
        }
    }

    // ฟังก์ชันเปลี่ยนข้อความตามประเภทที่เลือก
    function updateUI(type) {
        if (type === 'adjust_perm') {
            labelName.innerHTML = "ชื่อ-นามสกุล / User ERP ที่ต้องการปรับสิทธิ์";
        } else {
            labelName.innerHTML = "ชื่อ-นามสกุล สำหรับเปิด User ใหม่";
        }
    }

    // --- Events ---
    loadFromLocal();

    // เปลี่ยน Radio แล้วเซฟ + อัปเดต UI
    document.querySelectorAll('input[name="request_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            updateUI(e.target.value);
            saveToLocal();
        });
    });

    document.getElementById("addNameBtn").addEventListener("click", () => {
        nameContainer.appendChild(createNewRow("name_en[]", "ชื่อ-นามสกุล"));
        saveToLocal();
    });

    document.getElementById("addModuleBtn").addEventListener("click", () => {
        moduleContainer.appendChild(createNewRow("erp_module[]", "รายละเอียดที่ต้องการ เช่น ใช้โปรไฟล์อะไร ต้องการเพิ่มอะไร"));
        saveToLocal();
    });

    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("remove-btn")) {
            e.target.closest('.d-flex').remove();
            saveToLocal();
        }
    });

    document.addEventListener("input", saveToLocal);

    document.querySelector('button[type="reset"]').addEventListener("click", (e) => {
        if (confirm("ต้องการล้างข้อมูลร่างทั้งหมดหรือไม่?")) {
            localStorage.removeItem('erp_form_data');
            setTimeout(() => location.reload(), 100);
        } else {
            e.preventDefault();
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const downloadBtn = document.getElementById("downloadBtn");

    function updateDownloadLink(type) {
        if (!downloadBtn) return;

        if (type === 'adjust_perm') {
            // ลิงก์สำหรับแบบฟอร์มขอปรับเปลี่ยนสิทธิ์ระบบ ERP [cite: 45, 76]
            downloadBtn.href = "/static/docs/IT-ERP-001_V1.pdf";
            downloadBtn.innerHTML = '<i class="fas fa-file-download me-1"></i> ดาวน์โหลดแบบฟอร์มปรับสิทธิ์ (IT-ERP-001)';
        } else {
            // ลิงก์สำหรับแบบฟอร์มขอเปิด User ในระบบ ERP [cite: 8, 39]
            downloadBtn.href = "/static/docs/IT-ERP-004_V1.pdf";
            downloadBtn.innerHTML = '<i class="fas fa-file-download me-1"></i> ดาวน์โหลดแบบฟอร์มเปิด User (IT-ERP-004)';
        }
    }

    // ตรวจจับการเปลี่ยน Radio Button
    document.querySelectorAll('input[name="request_type"]').forEach(radio => {
        radio.addEventListener('change', function(e) {
            updateDownloadLink(e.target.value);
        });
    });

    // เรียกใช้ครั้งแรกเมื่อโหลดหน้า
    const checkedType = document.querySelector('input[name="request_type"]:checked');
    if (checkedType) updateDownloadLink(checkedType.value);
});