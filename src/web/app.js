/* global pywebview */

(function () {
  'use strict';

  let modalResolve = null;
  let modalReject = null;
  let focusTrapHandler = null;
  let updateInfo = null;

  function api() {
    return window.pywebview && window.pywebview.api;
  }

  function uiLog(msg) {
    const fn = api();
    if (fn && fn.log_js) {
      fn.log_js(String(msg)).catch(function () {});
    }
  }

  window.showAlert = function (message, type) {
    type = type || 'info';
    const region = document.getElementById('alert-region');
    if (!region) return;
    region.textContent = message;
    region.className = 'alert-region ' + type;
    region.classList.remove('hidden');
    clearTimeout(window._alertTimer);
    window._alertTimer = setTimeout(function () {
      region.classList.add('hidden');
    }, 4500);
  };

  window.showModal = function (options) {
    return new Promise(function (resolve, reject) {
      const overlay = document.getElementById('modal-overlay');
      const modal = document.getElementById('modal');
      const titleEl = document.getElementById('modal-title');
      const bodyEl = document.getElementById('modal-body');
      const footerEl = document.getElementById('modal-footer');
      if (!overlay || !modal) {
        reject(new Error('Modal elements missing'));
        return;
      }

      modalResolve = resolve;
      modalReject = reject;

      titleEl.textContent = options.title || '';
      bodyEl.innerHTML = options.bodyHtml || '';
      footerEl.innerHTML = options.footerHtml || '';
      modal.classList.toggle('modal-wide', !!options.wide);

      overlay.classList.remove('hidden');
      overlay.setAttribute('aria-hidden', 'false');

      const focusable = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length) focusable[0].focus();

      focusTrapHandler = function (e) {
        if (e.key === 'Escape' && options.closable !== false) {
          window.hideModal(options.dismissValue);
        }
        if (e.key === 'Tab' && focusable.length) {
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      };
      document.addEventListener('keydown', focusTrapHandler);
    });
  };

  window.hideModal = function (value) {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
      overlay.classList.add('hidden');
      overlay.setAttribute('aria-hidden', 'true');
    }
    if (focusTrapHandler) {
      document.removeEventListener('keydown', focusTrapHandler);
      focusTrapHandler = null;
    }
    if (modalResolve) {
      const r = modalResolve;
      modalResolve = null;
      modalReject = null;
      r(value);
    }
  };

  window.onerror = function (msg, src, line, col, err) {
    uiLog('Error: ' + msg + ' at ' + src + ':' + line);
    showAlert('JavaScript error: ' + msg, 'error');
  };

  window.addEventListener('unhandledrejection', function (e) {
    uiLog('Unhandled rejection: ' + e.reason);
    showAlert('Error: ' + e.reason, 'error');
  });

  document.getElementById('modal-close').addEventListener('click', function () {
    hideModal(undefined);
  });

  window.on_break_reminder = function (data) {
    showAlert((data && data.message) || "It's time to take a break.", 'info');
    if (window.DashboardUI && window.DashboardUI.onBreakReminder) {
      window.DashboardUI.onBreakReminder();
    }
  };

  function showUpdateModal(info) {
    updateInfo = info;
    const overlay = document.getElementById('update-modal');
    document.getElementById('update-modal-version').textContent =
      'Version ' +
      info.latest_version +
      ' is available (you have ' +
      (info.current_version || 'unknown') +
      ').';
    document.getElementById('update-modal-notes').textContent = info.notes || '';
    if (overlay) {
      overlay.classList.remove('hidden');
      overlay.setAttribute('aria-hidden', 'false');
    }
  }

  function hideUpdateModal() {
    const overlay = document.getElementById('update-modal');
    if (overlay) {
      overlay.classList.add('hidden');
      overlay.setAttribute('aria-hidden', 'true');
    }
    updateInfo = null;
  }

  async function checkForUpdates(force) {
    try {
      const r = await api().check_for_updates(!!force);
      if (!r || r.status !== 'success') {
        showAlert((r && r.message) || 'Update check failed', 'error');
        return;
      }
      if (r.available || r.update_available) {
        showUpdateModal(r);
      } else if (force) {
        const msgs = {
          up_to_date: 'You are up to date.',
          recently_checked: 'Checked recently. Try again later.',
          snooze: 'Update snoozed.',
          skipped: 'This version was skipped.',
          offline: 'Could not reach update server.',
          disabled: 'Update checks are disabled.',
        };
        showAlert(msgs[r.reason] || 'No update available.', r.reason === 'offline' ? 'error' : 'info');
      }
    } catch (e) {
      showAlert('Update check error: ' + e, 'error');
    }
  }

  function setupUpdateHandlers() {
    const btn = document.getElementById('btn-check-updates');
    if (btn) btn.addEventListener('click', function () { checkForUpdates(true); });

    const downloadBtn = document.getElementById('update-download');
    if (downloadBtn) {
      downloadBtn.addEventListener('click', async function () {
        if (!updateInfo) return;
        const url = updateInfo.installer_url || updateInfo.release_page;
        await api().open_update_download(url);
        hideUpdateModal();
      });
    }

    const laterBtn = document.getElementById('update-later');
    if (laterBtn) {
      laterBtn.addEventListener('click', async function () {
        if (!updateInfo) return;
        await api().dismiss_update_notice(updateInfo.latest_version, 'later');
        hideUpdateModal();
      });
    }

    const skipBtn = document.getElementById('update-skip');
    if (skipBtn) {
      skipBtn.addEventListener('click', async function () {
        if (!updateInfo) return;
        await api().dismiss_update_notice(updateInfo.latest_version, 'skip');
        hideUpdateModal();
      });
    }
  }

  window.addEventListener('pywebviewready', async function () {
    const startup = document.getElementById('startup-overlay');
    try {
      const r = await api().prepare_startup();
      if (!r || r.status !== 'success') {
        showAlert((r && r.message) || 'Startup failed', 'error');
        if (startup) startup.innerHTML = '<p>Startup failed. See alert.</p>';
        return;
      }
      if (startup) startup.classList.add('hidden');

      setupUpdateHandlers();

      const data = await api().get_initial_data();
      if (data.status !== 'success') {
        showAlert(data.message || 'Failed to load initial data', 'error');
        return;
      }

      const versionEl = document.getElementById('app-version');
      if (versionEl && data.version) versionEl.textContent = 'v' + data.version;

      if (window.DashboardUI) await window.DashboardUI.init(data);
      if (window.CategoriesUI) window.CategoriesUI.init(data);
      if (window.GraphUI) window.GraphUI.init();
      if (window.ExportUI) window.ExportUI.init();
      await checkForUpdates(false);
    } catch (e) {
      showAlert('Startup error: ' + e, 'error');
      if (startup) startup.innerHTML = '<p>Startup error.</p>';
    }
  });
})();
