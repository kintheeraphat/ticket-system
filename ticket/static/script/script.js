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
// TestChartหน้าDashboard
