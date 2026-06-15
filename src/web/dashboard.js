(function () {
  'use strict';

  let pollTimer = null;
  let breakTimerRunning = false;
  let playIconUri = '';
  let pauseIconUri = '';

  function api() {
    return window.pywebview.api;
  }

  function renderCategories(summary) {
    const list = document.getElementById('categories-list');
    if (!list) return;
    list.innerHTML = '';
    if (!summary || !summary.length) {
      const li = document.createElement('li');
      li.textContent = 'No activity logged yet or no categories found.';
      list.appendChild(li);
      return;
    }
    summary.forEach(function (item) {
      const li = document.createElement('li');
      const name = String(item.category || '').padEnd(25, ' ');
      const count = String(item.count || 0).padStart(5, ' ');
      const pct = String(item.percentage || 0).padStart(6, ' ');
      li.textContent = name + ' (' + count + ' entries | ' + pct + '%)';
      list.appendChild(li);
    });
  }

  function updateBreakIcon() {
    const img = document.getElementById('break-toggle-icon');
    if (!img) return;
    img.src = breakTimerRunning ? pauseIconUri : playIconUri;
  }

  async function pollDashboard() {
    try {
      const r = await api().get_dashboard_state();
      if (r.status !== 'success') return;

      document.getElementById('current-app-time').textContent =
        'Current App Time: ' + (r.current_app_time || '00:00:00');
      document.getElementById('active-window').textContent =
        'Active: ' + (r.active_window || 'None');
      document.getElementById('previous-window').textContent =
        'Previous: ' + (r.previous_window || 'None');
      document.getElementById('break-interval-label').textContent =
        'Break Interval: ' + (r.break_interval_display || '--');
      document.getElementById('break-countdown-label').textContent =
        'Time Until Next Break: ' + (r.break_countdown_display || '--');

      breakTimerRunning = !!r.break_timer_running;
      updateBreakIcon();
      renderCategories(r.categories_summary);
      if (r.break_reminder) {
        showAlert("It's time to take a break.", 'info');
        if (window.DashboardUI && window.DashboardUI.onBreakReminder) {
          window.DashboardUI.onBreakReminder();
        }
      }
      if (r.category_prompt && window.CategoriesUI && window.CategoriesUI.showCategoryPrompt) {
        setTimeout(function () {
          window.CategoriesUI.showCategoryPrompt(r.category_prompt);
        }, 0);
      }
    } catch (e) {
      /* ignore transient poll errors */
    }
  }

  async function showBreakIntervalModal(minMinutes) {
    const bodyHtml =
      '<div class="form-row">' +
      '<label for="break-minutes">New interval (minutes, min ' + minMinutes + '):</label>' +
      '<input type="number" id="break-minutes" min="' + minMinutes + '" step="1">' +
      '</div>';
    const footerHtml =
      '<button type="button" class="btn" id="modal-cancel">Cancel</button>' +
      '<button type="button" class="btn" id="modal-ok">Set</button>';

    showModal({ title: 'Set Break Interval', bodyHtml: bodyHtml, footerHtml: footerHtml }).then(
      async function (ok) {
        if (!ok) return;
        const input = document.getElementById('break-minutes');
        const r = await api().set_break_interval(parseInt(input.value, 10));
        if (r.status === 'success') {
          showAlert('Break interval updated.', 'success');
          pollDashboard();
        } else {
          showAlert(r.message || 'Invalid interval', 'error');
        }
      }
    );

    setTimeout(function () {
      document.getElementById('modal-cancel').onclick = function () {
        hideModal(false);
      };
      document.getElementById('modal-ok').onclick = function () {
        hideModal(true);
      };
      const input = document.getElementById('break-minutes');
      if (input) input.focus();
    }, 0);
  }

  async function confirmExit() {
    const bodyHtml = '<p>Are you sure you want to close Time Tracker?</p>';
    const footerHtml =
      '<button type="button" class="btn" id="modal-no">No</button>' +
      '<button type="button" class="btn btn-close" id="modal-yes">Yes</button>';

    showModal({ title: 'Confirm Exit', bodyHtml: bodyHtml, footerHtml: footerHtml }).then(
      async function (yes) {
        if (yes) await api().exit_app();
      }
    );

    setTimeout(function () {
      document.getElementById('modal-no').onclick = function () {
        hideModal(false);
      };
      document.getElementById('modal-yes').onclick = function () {
        hideModal(true);
      };
    }, 0);
  }

  window.DashboardUI = {
    init: async function (initialData) {
      playIconUri = initialData.play_icon_uri || '';
      pauseIconUri = initialData.pause_icon_uri || '';
      breakTimerRunning = false;
      updateBreakIcon();
      renderCategories(initialData.categories_summary);

      document.getElementById('break-interval-label').textContent =
        'Break Interval: ' +
        String(initialData.break_interval_minutes || 50).padStart(2, '0') +
        ':00:00';

      document.getElementById('btn-set-break').onclick = function () {
        showBreakIntervalModal(initialData.min_break_minutes || 10);
      };

      document.getElementById('btn-reset-break').onclick = async function () {
        const r = await api().reset_break_countdown();
        if (r.status === 'success') pollDashboard();
      };

      document.getElementById('btn-toggle-break').onclick = async function () {
        const r = await api().toggle_break_timer(!breakTimerRunning);
        if (r.status === 'success') {
          breakTimerRunning = r.break_timer_running;
          updateBreakIcon();
        } else {
          showAlert(r.message || 'Failed to toggle break timer', 'error');
        }
      };

      document.getElementById('btn-edit-categories').onclick = function () {
        if (window.CategoriesUI) window.CategoriesUI.openEditModal();
      };

      document.getElementById('btn-show-graph').onclick = function () {
        if (window.GraphUI) window.GraphUI.open();
      };

      document.getElementById('btn-export').onclick = function () {
        if (window.ExportUI) window.ExportUI.open();
      };

      document.getElementById('btn-close').onclick = confirmExit;

      pollDashboard();
      pollTimer = setInterval(pollDashboard, 1000);
    },

    onBreakReminder: async function () {
      await pollDashboard();
    },
  };
})();
