(function () {
  'use strict';

  function api() {
    return window.pywebview.api;
  }

  function todayStr() {
    const d = new Date();
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return dd + '/' + mm + '/' + yyyy;
  }

  function monthStartStr() {
    const d = new Date();
    const dd = '01';
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return dd + '/' + mm + '/' + yyyy;
  }

  window.ExportUI = {
    init: function () {},

    open: function () {
      const bodyHtml =
        '<p>Report type:</p>' +
        '<div class="radio-group">' +
        '<label><input type="radio" name="export-type" value="all" checked> All Data</label>' +
        '<label><input type="radio" name="export-type" value="range"> Date Range</label>' +
        '</div>' +
        '<div id="date-fields" class="date-fields disabled">' +
        '<div class="form-row"><label>Start (DD/MM/YYYY)</label>' +
        '<input type="text" id="export-start" value="' +
        monthStartStr() +
        '"></div>' +
        '<div class="form-row"><label>End (DD/MM/YYYY)</label>' +
        '<input type="text" id="export-end" value="' +
        todayStr() +
        '"></div></div>';

      const footerHtml =
        '<button type="button" class="btn" id="export-cancel">Cancel</button>' +
        '<button type="button" class="btn" id="export-run">Generate and Export</button>';

      showModal({
        title: 'Export Report Options',
        bodyHtml: bodyHtml,
        footerHtml: footerHtml,
      }).then(function () {});

      setTimeout(function () {
        const dateFields = document.getElementById('date-fields');
        document.querySelectorAll('input[name="export-type"]').forEach(function (radio) {
          radio.onchange = function () {
            if (radio.value === 'range' && radio.checked) {
              dateFields.classList.remove('disabled');
            } else if (radio.value === 'all' && radio.checked) {
              dateFields.classList.add('disabled');
            }
          };
        });

        document.getElementById('export-cancel').onclick = function () {
          hideModal(false);
        };

        document.getElementById('export-run').onclick = async function () {
          const exportType =
            document.querySelector('input[name="export-type"]:checked').value;
          let startDate = null;
          let endDate = null;
          if (exportType === 'range') {
            startDate = document.getElementById('export-start').value.trim();
            endDate = document.getElementById('export-end').value.trim();
            if (!startDate || !endDate) {
              showAlert('Please provide start and end dates.', 'error');
              return;
            }
          }

          const pick = await api().pick_save_path('', 'activity_report.csv');
          if (pick.status !== 'success') {
            showAlert(pick.message || 'File picker failed', 'error');
            return;
          }
          if (pick.cancelled || !pick.path) {
            hideModal(false);
            return;
          }

          const r = await api().export_report({
            path: pick.path,
            export_type: exportType,
            start_date: startDate,
            end_date: endDate,
          });

          if (r.status === 'success') {
            showAlert('Report exported to ' + r.path, 'success');
            hideModal(true);
          } else {
            showAlert(r.message || 'Export failed', 'error');
          }
        };
      }, 0);
    },
  };
})();
