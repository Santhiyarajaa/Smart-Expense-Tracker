// ---------------------------------------------------------------------
// dashboard.js
// Handles: mobile sidebar toggle, Chart.js rendering on the dashboard,
// and live category-prediction preview on the add/edit expense forms.
// ---------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
    // Mobile sidebar (drawer) toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    function openDrawer() {
        if (sidebar) sidebar.classList.add('show');
        if (sidebarBackdrop) sidebarBackdrop.classList.add('show');
    }

    function closeDrawer() {
        if (sidebar) sidebar.classList.remove('show');
        if (sidebarBackdrop) sidebarBackdrop.classList.remove('show');
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            if (sidebar.classList.contains('show')) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    }

    // Tapping the backdrop closes the drawer
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', closeDrawer);
    }

    // Selecting any nav item closes the drawer automatically (mobile only)
    if (sidebar) {
        sidebar.querySelectorAll('.sidebar-nav a').forEach(function (link) {
            link.addEventListener('click', closeDrawer);
        });
    }

    // ---------------- Dashboard charts ----------------
    if (window.dashboardData && typeof Chart !== 'undefined') {
        const data = window.dashboardData;

        const categoryCanvas = document.getElementById('categoryChart');
        if (categoryCanvas && data.categoryLabels.length > 0) {
            new Chart(categoryCanvas, {
                type: 'doughnut',
                data: {
                    labels: data.categoryLabels,
                    datasets: [{
                        data: data.categoryValues,
                        backgroundColor: [
                            '#7c3aed', '#2563eb', '#14b8a6', '#f59e0b',
                            '#ef4444', '#a855f7', '#0ea5e9', '#22c55e', '#94a3b8'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        const trendCanvas = document.getElementById('trendChart');
        if (trendCanvas && data.trendLabels.length > 0) {
            new Chart(trendCanvas, {
                type: 'line',
                data: {
                    labels: data.trendLabels,
                    datasets: [{
                        label: 'Daily Spending (₹)',
                        data: data.trendValues,
                        borderColor: '#5b21b6',
                        backgroundColor: 'rgba(124,58,237,0.15)',
                        tension: 0.3,
                        fill: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    }

    // ---------------- Live category prediction ----------------
    const descriptionInput = document.getElementById('id_description');
    const predictedCategoryEl = document.getElementById('predictedCategory');

    if (descriptionInput && predictedCategoryEl && typeof predictUrl !== 'undefined') {
        let debounceTimer;
        descriptionInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const description = descriptionInput.value.trim();
            if (!description) {
                predictedCategoryEl.textContent = 'Other';
                return;
            }
            debounceTimer = setTimeout(function () {
                fetch(predictUrl + '?description=' + encodeURIComponent(description))
                    .then(function (response) { return response.text(); })
                    .then(function (category) {
                        predictedCategoryEl.textContent = category;
                    })
                    .catch(function () {
                        // Fail silently - category will still be predicted server-side on save.
                    });
            }, 300);
        });
    }
});
