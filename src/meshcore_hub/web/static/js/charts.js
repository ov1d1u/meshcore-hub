/**
 * MeshCore Hub - Chart.js Helpers
 *
 * Provides common chart configuration and initialization helpers
 * for activity charts used on home and dashboard pages.
 */

/**
 * OKLCH color values for consistent theming
 */
const ChartColors = {
    // Primary (purple/blue)
    primary: 'oklch(0.65 0.24 265)',
    primaryFill: 'oklch(0.65 0.24 265 / 0.1)',

    // Secondary (pink/magenta)
    secondary: 'oklch(0.7 0.17 330)',
    secondaryFill: 'oklch(0.7 0.17 330 / 0.1)',

    // Accent (teal/cyan)
    accent: 'oklch(0.75 0.18 180)',
    accentFill: 'oklch(0.75 0.18 180 / 0.1)',

    // Neutral grays
    grid: 'oklch(0.4 0 0 / 0.2)',
    text: 'oklch(0.7 0 0)',
    tooltipBg: 'oklch(0.25 0 0)',
    tooltipText: 'oklch(0.9 0 0)',
    tooltipBorder: 'oklch(0.4 0 0)'
};

/**
 * Create common chart options with optional legend
 * @param {boolean} showLegend - Whether to show the legend
 * @returns {Object} Chart.js options object
 */
function createChartOptions(showLegend) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: showLegend,
                position: 'bottom',
                labels: {
                    color: ChartColors.text,
                    boxWidth: 12,
                    padding: 8
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: ChartColors.tooltipBg,
                titleColor: ChartColors.tooltipText,
                bodyColor: ChartColors.tooltipText,
                borderColor: ChartColors.tooltipBorder,
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: { color: ChartColors.grid },
                ticks: {
                    color: ChartColors.text,
                    maxRotation: 45,
                    minRotation: 45,
                    maxTicksLimit: 10
                }
            },
            y: {
                beginAtZero: true,
                grid: { color: ChartColors.grid },
                ticks: {
                    color: ChartColors.text,
                    precision: 0
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };
}

/**
 * Format date labels for chart display (e.g., "8 Feb")
 * @param {Array} data - Array of objects with 'date' property
 * @returns {Array} Formatted date strings
 */
function formatDateLabels(data) {
    return data.map(function(d) {
        var date = new Date(d.date);
        return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    });
}

/**
 * Create a single-dataset line chart
 * @param {string} canvasId - ID of the canvas element
 * @param {Object} data - Data object with 'data' array containing {date, count} objects
 * @param {string} label - Dataset label
 * @param {string} borderColor - Line color
 * @param {string} backgroundColor - Fill color
 * @param {boolean} fill - Whether to fill under the line
 */
function createLineChart(canvasId, data, label, borderColor, backgroundColor, fill) {
    var ctx = document.getElementById(canvasId);
    if (!ctx || !data || !data.data || data.data.length === 0) {
        return null;
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: formatDateLabels(data.data),
            datasets: [{
                label: label,
                data: data.data.map(function(d) { return d.count; }),
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                fill: fill,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: createChartOptions(false)
    });
}

/**
 * Create a multi-dataset activity chart (for home page)
 * @param {string} canvasId - ID of the canvas element
 * @param {Object} advertData - Advertisement data with 'data' array
 * @param {Object} messageData - Message data with 'data' array
 */
function createActivityChart(canvasId, advertData, messageData) {
    var ctx = document.getElementById(canvasId);
    if (!ctx || !advertData || !advertData.data || advertData.data.length === 0) {
        return null;
    }

    var labels = formatDateLabels(advertData.data);
    var advertCounts = advertData.data.map(function(d) { return d.count; });
    var messageCounts = messageData && messageData.data
        ? messageData.data.map(function(d) { return d.count; })
        : [];

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Advertisements',
                data: advertCounts,
                borderColor: ChartColors.secondary,
                backgroundColor: ChartColors.secondaryFill,
                fill: false,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5
            }, {
                label: 'Messages',
                data: messageCounts,
                borderColor: ChartColors.accent,
                backgroundColor: ChartColors.accentFill,
                fill: false,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: createChartOptions(true)
    });
}

/**
 * Initialize dashboard charts (nodes, advertisements, messages)
 * @param {Object} nodeData - Node count data
 * @param {Object} advertData - Advertisement data
 * @param {Object} messageData - Message data
 */
function initDashboardCharts(nodeData, advertData, messageData) {
    // Node count chart (primary color)
    createLineChart(
        'nodeChart',
        nodeData,
        'Total Nodes',
        ChartColors.primary,
        ChartColors.primaryFill,
        true
    );

    // Advertisements chart (secondary color)
    createLineChart(
        'advertChart',
        advertData,
        'Advertisements',
        ChartColors.secondary,
        ChartColors.secondaryFill,
        true
    );

    // Messages chart (accent color)
    createLineChart(
        'messageChart',
        messageData,
        'Messages',
        ChartColors.accent,
        ChartColors.accentFill,
        true
    );
}
