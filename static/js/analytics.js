document.addEventListener("DOMContentLoaded", () => {

    const colors = {
        primary: "#2563eb",
        teal: "#0f766e",
        violet: "#7c3aed",
        amber: "#d97706",
        danger: "#dc2626",
        slate: "#64748b",
        grid: "rgba(148, 163, 184, .18)",
        palette: [
            "#2563eb",
            "#0f766e",
            "#7c3aed",
            "#d97706",
            "#dc2626",
            "#0891b2"
        ],
    };


    function load(id) {
        const element = document.getElementById(id);

        if (!element) {
            console.warn("Analytics data element not found:", id);
            return [];
        }

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            console.error("Unable to parse analytics data:", id, error);
            return [];
        }
    }


    function chartOptions({
        legend = false,
        scales = false
    } = {}) {

        return {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {

                legend: {
                    display: legend,
                    position: "bottom",

                    labels: {
                        usePointStyle: true,
                        boxWidth: 8,
                        padding: 18,
                        color: colors.slate,
                    },
                },

                tooltip: {
                    backgroundColor: "#0f172a",
                    padding: 12,
                    displayColors: false,
                },
            },

            scales: scales
                ? {
                    x: {
                        grid: {
                            display: false,
                        },

                        ticks: {
                            color: colors.slate,
                        },
                    },

                    y: {
                        beginAtZero: true,

                        grid: {
                            color: colors.grid,
                        },

                        ticks: {
                            color: colors.slate,
                            precision: 0,
                        },
                    },
                }
                : undefined,
        };
    }


    const predictionTrend =
        load("prediction-trend-data");

    const diseaseDistribution =
        load("disease-distribution-data");

    const moduleDistribution =
        load("module-distribution-data");

    const ageDistribution =
        load("age-distribution-data");

    const genderDistribution =
        load("gender-distribution-data");

    const lifestyleDistribution =
        load("lifestyle-distribution-data");


    /* =====================================================
       PREDICTION TREND
       Backend: month, total
    ===================================================== */

    const predictionTrendChart =
        document.getElementById("predictionTrendChart");

    if (predictionTrendChart && predictionTrend.length) {

        new Chart(
            predictionTrendChart,
            {
                type: "line",

                data: {
                    labels: predictionTrend.map(
                        item => item.month
                    ),

                    datasets: [
                        {
                            label: "Predictions",

                            data: predictionTrend.map(
                                item => item.total
                            ),

                            borderColor: colors.primary,

                            backgroundColor:
                                "rgba(37, 99, 235, .12)",

                            borderWidth: 3,

                            pointRadius: 3,

                            pointHoverRadius: 5,

                            fill: true,

                            tension: 0.4,

                            spanGaps: true,
                        }
                    ],
                },

                options: chartOptions({
                    scales: true,
                }),
            }
        );
    }


    /* =====================================================
       DISEASE DISTRIBUTION
       Backend: label, count
    ===================================================== */

    const diseaseDistributionChart =
        document.getElementById(
            "diseaseDistributionChart"
        );

    if (
        diseaseDistributionChart &&
        diseaseDistribution.length
    ) {

        new Chart(
            diseaseDistributionChart,
            {
                type: "doughnut",

                data: {
                    labels: diseaseDistribution.map(
                        item => item.label
                    ),

                    datasets: [
                        {
                            data: diseaseDistribution.map(
                                item => item.count
                            ),

                            backgroundColor:
                                colors.palette,

                            borderColor: "#ffffff",

                            borderWidth: 4,
                        }
                    ],
                },

                options: chartOptions({
                    legend: true,
                }),
            }
        );
    }


    /* =====================================================
       PREDICTION MODULE DISTRIBUTION
       Backend: label, count
    ===================================================== */

    const moduleDistributionChart =
        document.getElementById(
            "moduleDistributionChart"
        );

    if (
        moduleDistributionChart &&
        moduleDistribution.length
    ) {

        new Chart(
            moduleDistributionChart,
            {
                type: "bar",

                data: {
                    labels: moduleDistribution.map(
                        item => item.label
                    ),

                    datasets: [
                        {
                            label: "Predictions",

                            data: moduleDistribution.map(
                                item => item.count
                            ),

                            backgroundColor:
                                colors.primary,

                            borderRadius: 7,

                            borderSkipped: false,
                        }
                    ],
                },

                options: chartOptions({
                    scales: true,
                }),
            }
        );
    }


    /* =====================================================
       AGE DISTRIBUTION
       Backend: group, count
    ===================================================== */

    const ageDistributionChart =
        document.getElementById(
            "ageDistributionChart"
        );

    if (
        ageDistributionChart &&
        ageDistribution.length
    ) {

        new Chart(
            ageDistributionChart,
            {
                type: "bar",

                data: {
                    labels: ageDistribution.map(
                        item => item.group
                    ),

                    datasets: [
                        {
                            label: "Patients",

                            data: ageDistribution.map(
                                item => item.count
                            ),

                            backgroundColor:
                                colors.violet,

                            borderRadius: 7,

                            borderSkipped: false,
                        }
                    ],
                },

                options: chartOptions({
                    scales: true,
                }),
            }
        );
    }


    /* =====================================================
       GENDER DISTRIBUTION
       Backend: label, count
    ===================================================== */

    const genderDistributionChart =
        document.getElementById(
            "genderDistributionChart"
        );

    if (
        genderDistributionChart &&
        genderDistribution.length
    ) {

        new Chart(
            genderDistributionChart,
            {
                type: "doughnut",

                data: {
                    labels: genderDistribution.map(
                        item => item.label
                    ),

                    datasets: [
                        {
                            data: genderDistribution.map(
                                item => item.count
                            ),

                            backgroundColor:
                                colors.palette,

                            borderColor: "#ffffff",

                            borderWidth: 4,
                        }
                    ],
                },

                options: chartOptions({
                    legend: true,
                }),
            }
        );
    }


    /* =====================================================
       LIFESTYLE DISTRIBUTION
       Backend: lifestyle, count
    ===================================================== */

    const lifestyleDistributionChart =
        document.getElementById(
            "lifestyleDistributionChart"
        );

    if (
        lifestyleDistributionChart &&
        lifestyleDistribution.length
    ) {

        new Chart(
            lifestyleDistributionChart,
            {
                type: "pie",

                data: {
                    labels: lifestyleDistribution.map(
                        item => item.lifestyle
                    ),

                    datasets: [
                        {
                            data: lifestyleDistribution.map(
                                item => item.count
                            ),

                            backgroundColor:
                                colors.palette,

                            borderColor: "#ffffff",

                            borderWidth: 4,
                        }
                    ],
                },

                options: chartOptions({
                    legend: true,
                }),
            }
        );
    }

});
