// SAD Central — Global Chart.js Themes and Configurations

// Custom colors matching Obsidian/Teal visual identity
const ChartColors = {
    teal: 'rgba(0, 242, 195, 0.5)',
    tealSolid: 'rgba(0, 242, 195, 1)',
    purple: 'rgba(141, 75, 255, 0.5)',
    purpleSolid: 'rgba(141, 75, 255, 1)',
    gridColor: 'rgba(255, 255, 255, 0.05)',
    textColor: 'rgba(255, 255, 255, 0.6)'
};

// Global Chart.js defaults configuration (if Chart.js is loaded)
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = ChartColors.textColor;
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.legend.labels.color = ChartColors.textColor;
}
