(function () {
  'use strict';

  let chartInstance = null;

  function api() {
    return window.pywebview.api;
  }

  function chartColors() {
    const root = getComputedStyle(document.documentElement);
    return {
      text: root.getPropertyValue('--chart-text').trim() || '#ffffff',
      grid: root.getPropertyValue('--chart-grid').trim() || 'rgba(128,128,128,0.3)',
      today: root.getPropertyValue('--chart-today').trim() || 'rgba(135, 206, 235, 0.85)',
      overall: root.getPropertyValue('--chart-overall').trim() || 'rgba(255, 165, 0, 0.85)',
      border: root.getPropertyValue('--chart-border').trim() || '#000000',
    };
  }

  function destroyChart() {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  }

  function renderStats(stats) {
    if (!stats) return 'No stats available.';
    return (
      'Displaying for: ' +
      stats.display_name +
      '\nToday: ' +
      stats.today +
      '\nThis Month: ' +
      stats.month +
      ' (' +
      stats.month_days +
      ' active day(s)). Productivity: ' +
      stats.month_productivity +
      '%\nOverall: ' +
      stats.overall +
      ' (' +
      stats.overall_days +
      ' total day(s) with data). Productivity: ' +
      stats.overall_productivity +
      '%'
    );
  }

  function renderTopPrograms(rows) {
    if (!rows || !rows.length) {
      return '<p>No program data for top ten.</p>';
    }
    const body = rows
      .map(function (row) {
        return (
          '<tr><td>' +
          escapeHtml(row.program_name) +
          '</td><td>' +
          escapeHtml(row.category) +
          '</td><td>' +
          escapeHtml(row.time_display) +
          '</td></tr>'
        );
      })
      .join('');
    return (
      '<table class="top-programs-table"><thead><tr><th>Program</th><th>Category</th><th>Time</th></tr></thead><tbody>' +
      body +
      '</tbody></table>'
    );
  }

  function renderChartSummaryTable(chartData) {
    const labels = (chartData && chartData.labels) || [];
    const today = (chartData && chartData.today_values) || [];
    const overall = (chartData && chartData.overall_values) || [];
    if (!labels.length) {
      return '<table class="visually-hidden" id="graph-chart-summary"><caption>Chart data</caption><tbody><tr><td>No chart data</td></tr></tbody></table>';
    }
    const rows = labels
      .map(function (label, i) {
        return (
          '<tr><th scope="row">' +
          escapeHtml(label) +
          '</th><td>' +
          escapeHtml(String(today[i] != null ? today[i] : '')) +
          '% today</td><td>' +
          escapeHtml(String(overall[i] != null ? overall[i] : '')) +
          '% overall</td></tr>'
        );
      })
      .join('');
    return (
      '<table class="visually-hidden" id="graph-chart-summary">' +
      '<caption>Category time percentages today and overall</caption>' +
      '<thead><tr><th scope="col">Category</th><th scope="col">Today</th><th scope="col">Overall</th></tr></thead>' +
      '<tbody>' +
      rows +
      '</tbody></table>'
    );
  }

  function updateChartAccessibility() {
    const canvas = document.getElementById('usage-chart');
    if (canvas) {
      canvas.setAttribute('role', 'img');
      canvas.setAttribute('aria-describedby', 'graph-stats graph-chart-summary');
    }
  }

  function drawChart(canvasId, chartData) {
    destroyChart();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !chartData) return;

    const colors = chartColors();
    const labels = chartData.labels || [];
    const ctx = canvas.getContext('2d');
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Today',
            data: chartData.today_values || [],
            backgroundColor: colors.today,
            borderColor: colors.border,
            borderWidth: 1,
          },
          {
            label: 'Overall',
            data: chartData.overall_values || [],
            backgroundColor: colors.overall,
            borderColor: colors.border,
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: colors.text },
          },
          title: {
            display: true,
            text: 'Category Time Percentage (Today vs Overall)',
            color: colors.text,
          },
        },
        scales: {
          x: {
            ticks: { color: colors.text, maxRotation: 25 },
            grid: { color: colors.grid },
          },
          y: {
            ticks: { color: colors.text },
            grid: { color: colors.grid },
            title: { display: true, text: 'Percentage of Time (%)', color: colors.text },
          },
        },
      },
    });
    updateChartAccessibility();
  }

  function refreshGraphView(data) {
    document.getElementById('graph-stats').textContent = renderStats(data.stats);
    const summaryEl = document.getElementById('graph-chart-summary-wrap');
    if (summaryEl) {
      summaryEl.innerHTML = renderChartSummaryTable(data.chart);
    }
    document.getElementById('top-programs').innerHTML = renderTopPrograms(data.top_programs);
    drawChart('usage-chart', data.chart);
  }

  async function loadGraphData(filterCategory) {
    const r = await api().graph_get_data(filterCategory || 'All Categories');
    if (r.status !== 'success') {
      showAlert(r.message || 'No data to display', 'info');
      return null;
    }
    return r;
  }

  window.GraphUI = {
    init: function () {},

    open: async function () {
      showLoading(true, 'Loading graph...');
      let data;
      try {
        data = await loadGraphData('All Categories');
      } finally {
        showLoading(false);
      }
      if (!data) return;

      const categoryOptions = (data.available_categories || ['All Categories'])
        .map(function (c) {
          return (
            '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</option>'
          );
        })
        .join('');

      const bodyHtml =
        '<div class="form-row"><label for="graph-category-filter">Filter category</label>' +
        '<select id="graph-category-filter">' +
        categoryOptions +
        '</select></div>' +
        '<pre id="graph-stats" class="graph-stats"></pre>' +
        '<div id="graph-chart-summary-wrap">' +
        renderChartSummaryTable(data.chart) +
        '</div>' +
        '<div class="graph-layout">' +
        '<div class="chart-container"><canvas id="usage-chart"></canvas></div>' +
        '<div id="top-programs">' +
        renderTopPrograms(data.top_programs) +
        '</div></div>';

      const footerHtml = '<button type="button" class="btn" id="graph-close">Close Graph</button>';

      showModal({
        title: 'Category Percentage Comparison',
        bodyHtml: bodyHtml,
        footerHtml: footerHtml,
        wide: true,
        onOpen: function () {
          refreshGraphView(data);
          document.getElementById('graph-close').onclick = function () {
            hideModal(true);
          };
          document.getElementById('graph-category-filter').onchange = async function (e) {
            showLoading(true, 'Refreshing graph...');
            try {
              const refreshed = await loadGraphData(e.target.value);
              if (refreshed) refreshGraphView(refreshed);
            } finally {
              showLoading(false);
            }
          };
        },
      }).then(function () {
        destroyChart();
      });
    },
  };
})();
