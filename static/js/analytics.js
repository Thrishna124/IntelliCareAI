document.addEventListener("DOMContentLoaded", () => {

    const colors = {
        primary: "#2563eb",
        teal: "#0f766e",
        violet: "#7c3aed",
        amber: "#d97706",
        danger: "#dc2626",
        slate: "#64748b",
        grid: "rgba(148, 163, 184, .18)",
        palette: ["#2563eb", "#0f766e", "#7c3aed", "#d97706", "#dc2626", "#0891b2"],
    };

    function load(id) {
        return JSON.parse(document.getElementById(id).textContent);
    }

    function chartOptions({ legend = false, scales = false } = {}) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: {
                    display: legend,
                    position: "bottom",
                    labels: { usePointStyle: true, boxWidth: 8, padding: 18, color: colors.slate },
                },
                tooltip: {
                    backgroundColor: "#0f172a",
                    padding: 12,
                    displayColors: false,
                },
            },
            scales: scales ? {
                x: { grid: { display: false }, ticks: { color: colors.slate } },
                y: { beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.slate, precision: 0 } },
            } : undefined,
        };
    }

    const predictionTrend = load("prediction-trend-data");
    const diseaseDistribution = load("disease-distribution-data");
    const moduleDistribution = load("module-distribution-data");
    const ageDistribution = load("age-distribution-data");
    const genderDistribution = load("gender-distribution-data");
    const lifestyleDistribution = load("lifestyle-distribution-data");


    new Chart(
        document.getElementById("predictionTrendChart"),
        {
            type: "line",
            data: {
                labels: predictionTrend.map(item => item.day),
                datasets: [{
                    label: "Predictions",
                    data: predictionTrend.map(item => item.total),
                    borderColor: colors.primary,
                    backgroundColor: "rgba(37, 99, 235, .12)",
                    borderWidth: 3,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.4,
                    spanGaps: true,
                }]
            },
            options: chartOptions({ scales: true })
        }
    );

    new Chart(
    document.getElementById("diseaseDistributionChart"),
    {
        type: "pie",
        data: {
            labels: diseaseDistribution.map(item => item.prediction),
            datasets: [{
                data: diseaseDistribution.map(item => item.total),
                backgroundColor: [colors.teal, colors.danger],
                borderColor: "#ffffff",
                borderWidth: 4,
            }]
        },
        options: chartOptions({ legend: true })
    }
);

    new Chart(
        document.getElementById("moduleDistributionChart"),
        {
            type: "bar",
            data: {
                labels: moduleDistribution.map(item => item.prediction_type),
                datasets: [{
                    label: "Predictions",
                    data: moduleDistribution.map(item => item.total),
                    backgroundColor: colors.primary,
                    borderRadius: 7,
                    borderSkipped: false,
                }]
            },
            options: chartOptions({ scales: true })
        }
    );
    
    new Chart(
        document.getElementById("ageDistributionChart"),
        {
            type: "bar",
            data: {
                labels: ageDistribution.map(item => item.group),
                datasets: [{
                    label: "Patients",
                    data: ageDistribution.map(item => item.total),
                    backgroundColor: colors.violet,
                    borderRadius: 7,
                    borderSkipped: false,
                }]
            },
            options: chartOptions({ scales: true })
        }
);
    
    new Chart(
        document.getElementById("genderDistributionChart"),
        {
            type: "doughnut",
            data: {
            labels: genderDistribution.map(item => item.sex),
            datasets: [{
                data: genderDistribution.map(item => item.total),
                backgroundColor: colors.palette,
                borderColor: "#ffffff",
                borderWidth: 4,
            }]
        },
        options: chartOptions({ legend: true })
    }
);
    

    new Chart(
        document.getElementById("lifestyleDistributionChart"),
        {
            type: "pie",
            data: {
            labels: lifestyleDistribution.map(item => item.lifestyle),
            datasets: [{
                data: lifestyleDistribution.map(item => item.total),
                backgroundColor: colors.palette,
                borderColor: "#ffffff",
                borderWidth: 4,
            }]
        },
        options: chartOptions({ legend: true })
    }
);

});
