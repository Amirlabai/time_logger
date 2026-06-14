(function () {
  'use strict';

  let chartInstance = null;

  function api() {
    return window.pywebview.api;
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
          row.program_name +
          '</td><td>' +
          row.category +
          '</td><td>' +
          row.time_display +
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

  function drawChart(canvasId, chartData) {
    destroyChart();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !chartData) return;

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
            backgroundColor: 'rgba(135, 206, 235, 0.85)',
            borderColor: '#000',
            borderWidth: 1,
          },
          {
            label: 'Overall',
            data: chartData.overall_values || [],
            backgroundColor: 'rgba(255, 165, 0, 0.85)',
            borderColor: '#000',
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#fff' },
          },
          title: {
            display: true,
            text: 'Category Time Percentage (Today vs Overall)',
            color: '#fff',
          },
        },
        scales: {
          x: {
            ticks: { color: '#fff', maxRotation: 25 },
            grid: { color: 'rgba(128,128,128,0.3)' },
          },
          y: {
            ticks: { color: '#fff' },
            grid: { color: 'rgba(128,128,128,0.3)' },
            title: { display: true, text: 'Percentage of Time (%)', color: '#fff' },
          },
        },
      },
    });
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
      const data = await loadGraphData('All Categories');
      if (!data) return;

      const categoryOptions = (data.available_categories || ['All Categories'])
        .map(function (c) {
          return '<option value="' + c + '">' + c + '</option>';
        })
        .join('');

      const bodyHtml =
        '<div class="form-row"><label>Filter category</label>' +
        '<select id="graph-category-filter">' +
        categoryOptions +
        '</select></div>' +
        '<pre id="graph-stats" class="graph-stats"></pre>' +
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
      }).then(function () {
        destroyChart();
      });

      setTimeout(function () {
        document.getElementById('graph-stats').textContent = renderStats(data.stats);
        drawChart('usage-chart', data.chart);
        document.getElementById('graph-close').onclick = function () {
          hideModal(true);
        };
        document.getElementById('graph-category-filter').onchange = async function (e) {
          const refreshed = await loadGraphData(e.target.value);
          if (!refreshed) return;
          document.getElementById('graph-stats').textContent = renderStats(refreshed.stats);
          document.getElementById('top-programs').innerHTML = renderTopPrograms(
            refreshed.top_programs
          );
          drawChart('usage-chart', refreshed.chart);
        };
      }, 0);
    },
  };
})();
