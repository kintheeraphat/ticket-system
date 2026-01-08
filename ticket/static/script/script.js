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
    console.log("ERP/VPN Form Loaded");

    const nameContainer = document.getElementById("nameFields");
    const moduleContainer = document.getElementById("moduleFields");

    // ฟังก์ชันช่วยสร้าง Row ใหม่
    function createNewRow(nameAttr, placeholder) {
        const div = document.createElement("div");
        div.className = "d-flex mb-2 animate-fade-in";
        div.innerHTML = `
            <input type="text" name="${nameAttr}" class="form-control me-2" placeholder="${placeholder}">
            <button type="button" class="btn btn-danger btn-sm remove-btn">ลบ</button>
        `;
        return div;
    }

    // เพิ่มชื่อ ERP
    document.getElementById("addNameBtn").addEventListener("click", function () {
        nameContainer.appendChild(createNewRow("name_en[]", "เช่น John Doe"));
    });

    // เพิ่มโมดูล ERP
    document.getElementById("addModuleBtn").addEventListener("click", function () {
        moduleContainer.appendChild(createNewRow("erp_module[]", "เช่น Sales, Accounting"));
    });

    // ลบแถว (ใช้ Event Delegation)
    document.addEventListener("click", function (e) {
        if (e.target && e.target.classList.contains("remove-btn")) {
            e.target.closest('.d-flex').remove();
        }
    });
});
