/* global pywebview */

(function () {
  'use strict';

  let modalResolve = null;
  let modalReject = null;
  let modalLastFocus = null;
  let modalOptions = null;
  let updateInfo = null;
  let blockingTrapHandler = null;

  const blockingLayers = { modal: 0, loading: 0 };
  const DEFAULT_LOADING_MESSAGE = 'Working...';

  function api() {
    return window.pywebview && window.pywebview.api;
  }

  function uiLog(msg) {
    const fn = api();
    if (fn && fn.log_js) {
      fn.log_js(String(msg)).catch(function () {});
    }
  }

  window.escapeHtml = function (text) {
    const d = document.createElement('div');
    d.textContent = text == null ? '' : String(text);
    return d.innerHTML;
  };

  function hideAlert() {
    const region = document.getElementById('alert-region');
    if (!region) return;
    region.classList.add('hidden');
    clearTimeout(window._alertTimer);
    window._alertTimer = null;
  }

  window.showAlert = function (message, type) {
    type = type || 'info';
    const region = document.getElementById('alert-region');
    const messageEl = document.getElementById('alert-message');
    if (!region || !messageEl) return;
    messageEl.textContent = message;
    region.className = 'alert-region ' + type;
    region.setAttribute('role', type === 'error' || type === 'warn' ? 'alert' : 'status');
    region.classList.remove('hidden');
    clearTimeout(window._alertTimer);
    window._alertTimer = null;
    if (type === 'info' || type === 'success') {
      window._alertTimer = setTimeout(hideAlert, 4500);
    }
  };

  function setAppAriaHidden(hidden) {
    const app = document.getElementById('app');
    if (app) app.setAttribute('aria-hidden', hidden ? 'true' : 'false');
  }

  function isBlocking() {
    return blockingLayers.modal > 0 || blockingLayers.loading > 0;
  }

  function getTopBlockingLayer() {
    if (blockingLayers.loading > 0) return 'loading';
    if (blockingLayers.modal > 0) return 'modal';
    return null;
  }

  function getFocusables(container) {
    if (!container) return [];
    return Array.prototype.slice.call(
      container.querySelectorAll(
        'button:not(.hidden):not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    );
  }

  function removeBlockingTrap() {
    if (blockingTrapHandler) {
      document.removeEventListener('keydown', blockingTrapHandler);
      blockingTrapHandler = null;
    }
  }

  function installBlockingTrap() {
    removeBlockingTrap();
    const layer = getTopBlockingLayer();
    if (!layer) return;

    blockingTrapHandler = function (e) {
      if (layer === 'modal' && e.key === 'Escape' && modalOptions && modalOptions.closable !== false) {
        window.hideModal(modalOptions.dismissValue);
        return;
      }
      if (e.key !== 'Tab') return;

      const container =
        layer === 'loading'
          ? document.getElementById('loading-overlay')
          : document.getElementById('modal');
      const focusable = getFocusables(container);
      if (!focusable.length) {
        e.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', blockingTrapHandler);
  }

  function syncBlockingState() {
    setAppAriaHidden(isBlocking());
    installBlockingTrap();
  }

  function acquireBlocking(reason) {
    if (blockingLayers[reason] !== undefined) {
      blockingLayers[reason] += 1;
    }
    syncBlockingState();
  }

  function releaseBlocking(reason) {
    if (blockingLayers[reason] > 0) {
      blockingLayers[reason] -= 1;
    }
    syncBlockingState();
  }

  function resolveInitialFocus(modal, options) {
    if (options.initialFocus) {
      if (typeof options.initialFocus === 'string') {
        return modal.querySelector(options.initialFocus);
      }
      return options.initialFocus;
    }
    const focusable = getFocusables(modal);
    const closeBtn = document.getElementById('modal-close');
    const withoutClose = focusable.filter(function (el) {
      return el !== closeBtn;
    });
    if (withoutClose.length) return withoutClose[0];
    if (focusable.length) return focusable[0];
    const titleEl = document.getElementById('modal-title');
    if (titleEl) {
      titleEl.setAttribute('tabindex', '-1');
      return titleEl;
    }
    return null;
  }

  window.showLoading = function (show, message) {
    const overlay = document.getElementById('loading-overlay');
    const textEl = document.getElementById('loading-message');
    if (!overlay) return;
    if (textEl) {
      textEl.textContent = message || DEFAULT_LOADING_MESSAGE;
    }
    if (show) {
      overlay.classList.remove('hidden');
      overlay.setAttribute('aria-hidden', 'false');
      overlay.setAttribute('aria-busy', 'true');
      acquireBlocking('loading');
      if (textEl) textEl.focus();
    } else {
      overlay.classList.add('hidden');
      overlay.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('aria-busy', 'false');
      releaseBlocking('loading');
    }
  };

  // Callers must escape dynamic strings in bodyHtml/footerHtml.
  window.showModal = function (options) {
    return new Promise(function (resolve, reject) {
      const overlay = document.getElementById('modal-overlay');
      const modal = document.getElementById('modal');
      const titleEl = document.getElementById('modal-title');
      const bodyEl = document.getElementById('modal-body');
      const footerEl = document.getElementById('modal-footer');
      const closeBtn = document.getElementById('modal-close');
      if (!overlay || !modal) {
        reject(new Error('Modal elements missing'));
        return;
      }

      modalResolve = resolve;
      modalReject = reject;
      modalLastFocus = document.activeElement;
      modalOptions = options;

      titleEl.textContent = options.title || '';
      bodyEl.innerHTML = options.bodyHtml || '';
      footerEl.innerHTML = options.footerHtml || '';
      modal.classList.toggle('modal-wide', !!options.wide);
      if (closeBtn) {
        closeBtn.classList.toggle('hidden', options.closable === false);
      }

      overlay.classList.remove('hidden');
      overlay.setAttribute('aria-hidden', 'false');
      acquireBlocking('modal');

      if (typeof options.onOpen === 'function') {
        options.onOpen(modal);
      }

      const focusTarget = resolveInitialFocus(modal, options);
      if (focusTarget && typeof focusTarget.focus === 'function') {
        focusTarget.focus();
      }
    });
  };

  window.hideModal = function (value) {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
      overlay.classList.add('hidden');
      overlay.setAttribute('aria-hidden', 'true');
    }
    releaseBlocking('modal');
    modalOptions = null;
    if (modalLastFocus && typeof modalLastFocus.focus === 'function') {
      modalLastFocus.focus();
    }
    modalLastFocus = null;
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

  document.getElementById('alert-dismiss').addEventListener('click', hideAlert);

  window.on_break_reminder = function (data) {
    showAlert((data && data.message) || "It's time to take a break.", 'warn');
    if (window.DashboardUI && window.DashboardUI.onBreakReminder) {
      window.DashboardUI.onBreakReminder();
    }
  };

  function showUpdateModal(info) {
    updateInfo = info;
    const versionText =
      'Version ' +
      info.latest_version +
      ' is available (you have ' +
      (info.current_version || 'unknown') +
      ').';
    const bodyHtml =
      '<p id="update-modal-version">' +
      escapeHtml(versionText) +
      '</p>' +
      '<p id="update-modal-notes">' +
      escapeHtml(info.notes || '') +
      '</p>' +
      '<p class="hint">Download the installer and run setup manually.</p>';
    const footerHtml =
      '<button type="button" class="btn" id="update-download">Download</button>' +
      '<button type="button" class="btn" id="update-later">Later</button>' +
      '<button type="button" class="btn" id="update-skip">Skip this version</button>';

    // closable: false — Later/Skip are intentional dismiss paths if download hangs.
    showModal({
      title: 'Update Available',
      bodyHtml: bodyHtml,
      footerHtml: footerHtml,
      closable: false,
      onOpen: function () {
        document.getElementById('update-download').onclick = async function () {
          if (!updateInfo) return;
          const btn = document.getElementById('update-download');
          const url = updateInfo.installer_url || updateInfo.release_page;
          btn.disabled = true;
          btn.textContent = 'Opening...';
          try {
            await api().open_update_download(url);
            hideUpdateModal();
          } catch (e) {
            showAlert('Download failed: ' + e, 'error');
            btn.disabled = false;
            btn.textContent = 'Download';
          }
        };
        document.getElementById('update-later').onclick = async function () {
          if (!updateInfo) return;
          await api().dismiss_update_notice(updateInfo.latest_version, 'later');
          hideUpdateModal();
        };
        document.getElementById('update-skip').onclick = async function () {
          if (!updateInfo) return;
          await api().dismiss_update_notice(updateInfo.latest_version, 'skip');
          hideUpdateModal();
        };
      },
    }).then(function () {
      updateInfo = null;
    });
  }

  function hideUpdateModal() {
    hideModal(true);
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

  function setStartupMessage(text) {
    const startup = document.getElementById('startup-overlay');
    const msgEl = document.getElementById('startup-message');
    if (msgEl) msgEl.textContent = text;
    if (startup) startup.setAttribute('aria-busy', 'false');
  }

  window.addEventListener('pywebviewready', async function () {
    const startup = document.getElementById('startup-overlay');
    try {
      const r = await api().prepare_startup();
      if (!r || r.status !== 'success') {
        showAlert((r && r.message) || 'Startup failed', 'error');
        setStartupMessage('Startup failed. See alert.');
        return;
      }
      if (startup) {
        startup.classList.add('hidden');
        startup.setAttribute('aria-busy', 'false');
      }

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

      document.getElementById('btn-check-updates').addEventListener('click', function () {
        checkForUpdates(true);
      });
      await checkForUpdates(false);
    } catch (e) {
      showAlert('Startup error: ' + e, 'error');
      setStartupMessage('Startup error.');
    }
  });
})();
