(function () {
  'use strict';

  let categoryNames = [];
  let programCategories = {};
  let editDraft = {};
  let promptOpen = false;
  let editStep = 'table';
  let editRowContext = { program: '', current: '' };
  let editShell = { title: '', footerHtml: '' };

  function api() {
    return window.pywebview.api;
  }

  function showCategoryPrompt(data) {
    if (!data || !data.program || promptOpen) return;
    if (window.isModalOpen && window.isModalOpen()) return;
    promptOpen = true;
    showPromptModal(data.program, data.categories || categoryNames);
  }

  window.on_category_prompt = showCategoryPrompt;

  async function showPromptModal(program, categories) {
    const options = (categories || [])
      .map(function (c) {
        return '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</option>';
      })
      .join('');

    const bodyHtml =
      '<p>Enter category for <strong>' +
      escapeHtml(program) +
      '</strong></p>' +
      '<div class="form-row"><label for="prompt-category-select">Available categories</label>' +
      '<select id="prompt-category-select"><option value="">-- select --</option>' +
      options +
      '</select></div>' +
      '<div class="form-row"><label for="prompt-category-new">Or enter new category</label>' +
      '<input type="text" id="prompt-category-new" placeholder="New category"></div>';

    const footerHtml =
      '<button type="button" class="btn" id="prompt-dismiss">Use Misc</button>' +
      '<button type="button" class="btn" id="prompt-submit">Submit</button>';

    showModal({
      title: 'Categorize: ' + program,
      bodyHtml: bodyHtml,
      footerHtml: footerHtml,
      closable: false,
      initialFocus: '#prompt-category-new',
      onOpen: function () {
        document.getElementById('prompt-dismiss').onclick = async function () {
          await api().dismiss_category(program);
          hideModal(true);
        };
        document.getElementById('prompt-submit').onclick = async function () {
          const selected = document.getElementById('prompt-category-select').value;
          const entered = document.getElementById('prompt-category-new').value.trim();
          let finalCat = 'Misc';
          if (entered) {
            finalCat = entered.replace(/\b\w/g, function (l) {
              return l.toUpperCase();
            });
          } else if (selected) {
            finalCat = selected;
          }
          const r = await api().submit_category(program, finalCat);
          if (r.status === 'success') {
            hideModal(true);
          } else {
            showAlert(r.message || 'Failed to save category', 'error');
          }
        };
      },
    }).then(function () {
      promptOpen = false;
    });
  }

  function renderProgramTable() {
    const programs = Object.keys(editDraft).sort();
    let rows = programs
      .map(function (name) {
        const cat = editDraft[name] || 'Misc';
        return (
          '<tr data-program="' +
          escapeHtml(name) +
          '"><td>' +
          escapeHtml(name) +
          '</td><td class="cat-cell">' +
          escapeHtml(cat) +
          '</td><td><button type="button" class="btn btn-edit-row">Edit</button></td></tr>'
        );
      })
      .join('');

    if (!rows) {
      rows = '<tr><td colspan="3">No programs in list.</td></tr>';
    }

    return (
      '<div class="program-table-wrap"><table class="program-table">' +
      '<thead><tr><th>Program</th><th>Category</th><th>Action</th></tr></thead>' +
      '<tbody id="program-table-body">' +
      rows +
      '</tbody></table></div>' +
      '<hr class="modal-divider">' +
      '<p><em>Add or update program in list</em></p>' +
      '<div class="form-row"><label for="new-program-name">Program name</label>' +
      '<input type="text" id="new-program-name"></div>' +
      '<div class="form-row"><label for="new-program-category">Category</label>' +
      '<select id="new-program-category">' +
      categoryNames
        .map(function (c) {
          return '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</option>';
        })
        .join('') +
      '</select></div>' +
      '<button type="button" class="btn" id="btn-add-program">Add/Update in List</button>'
    );
  }

  function renderRowEditBody(program, current) {
    const options = categoryNames
      .map(function (c) {
        const sel = c === current ? ' selected' : '';
        return '<option value="' + escapeHtml(c) + '"' + sel + '>' + escapeHtml(c) + '</option>';
      })
      .join('');

    return (
      '<p>Program: <strong>' +
      escapeHtml(program) +
      '</strong></p>' +
      '<div class="form-row"><label for="edit-row-select">Select category</label>' +
      '<select id="edit-row-select">' +
      options +
      '</select></div>' +
      '<div class="form-row"><label for="edit-row-new">Or new category</label>' +
      '<input type="text" id="edit-row-new"></div>'
    );
  }

  function renderConfirmHistoricalBody() {
    return (
      '<p>Update historical log entries for changed programs?</p>' +
      '<p class="hint">This might take a moment and cannot be undone easily.</p>'
    );
  }

  function renderEditStep() {
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');
    const footerEl = document.getElementById('modal-footer');
    if (!titleEl || !bodyEl || !footerEl) return;

    if (editStep === 'table') {
      titleEl.textContent = editShell.title;
      bodyEl.innerHTML = renderProgramTable();
      footerEl.innerHTML = editShell.footerHtml;
      bindEditModalEvents();
      bindEditModalFooter();
      return;
    }

    if (editStep === 'row') {
      titleEl.textContent = 'Set Category for: ' + editRowContext.program;
      bodyEl.innerHTML = renderRowEditBody(editRowContext.program, editRowContext.current);
      footerEl.innerHTML =
        '<button type="button" class="btn" id="edit-row-cancel">Cancel</button>' +
        '<button type="button" class="btn" id="edit-row-ok">OK</button>';
      document.getElementById('edit-row-cancel').onclick = function () {
        editStep = 'table';
        renderEditStep();
      };
      document.getElementById('edit-row-ok').onclick = function () {
        const entered = document.getElementById('edit-row-new').value.trim();
        const selected = document.getElementById('edit-row-select').value;
        let newCat = editRowContext.current;
        if (entered) {
          newCat = entered.replace(/\b\w/g, function (l) {
            return l.toUpperCase();
          });
          if (categoryNames.indexOf(newCat) === -1) categoryNames.push(newCat);
        } else if (selected) {
          newCat = selected;
        }
        editDraft[editRowContext.program] = newCat;
        editStep = 'table';
        renderEditStep();
      };
      return;
    }

    if (editStep === 'confirm') {
      titleEl.textContent = 'Update historical entries?';
      bodyEl.innerHTML = renderConfirmHistoricalBody();
      footerEl.innerHTML =
        '<button type="button" class="btn" id="hist-no">No</button>' +
        '<button type="button" class="btn" id="hist-yes">Yes</button>';
      return;
    }
  }

  function showEditTableView() {
    editStep = 'table';
    renderEditStep();
  }

  function showEditRowView(program, current) {
    editStep = 'row';
    editRowContext = { program: program, current: current };
    renderEditStep();
  }

  function bindEditModalEvents() {
    document.querySelectorAll('.btn-edit-row').forEach(function (btn) {
      btn.onclick = function () {
        const tr = btn.closest('tr');
        const program = tr.getAttribute('data-program');
        const cat = editDraft[program] || 'Misc';
        showEditRowView(program, cat);
      };
    });

    const addBtn = document.getElementById('btn-add-program');
    if (addBtn) {
      addBtn.onclick = function () {
        const name = document.getElementById('new-program-name').value.trim();
        const cat = document.getElementById('new-program-category').value;
        if (!name || !cat) {
          showAlert('Program name and category cannot be empty.', 'error');
          return;
        }
        editDraft[name] = cat;
        if (categoryNames.indexOf(cat) === -1) categoryNames.push(cat);
        document.getElementById('new-program-name').value = '';
        const bodyEl = document.getElementById('modal-body');
        if (bodyEl) {
          bodyEl.innerHTML = renderProgramTable();
          bindEditModalEvents();
        }
      };
    }
  }

  function confirmHistoricalUpdate() {
    return new Promise(function (resolve) {
      const titleEl = document.getElementById('modal-title');
      const bodyEl = document.getElementById('modal-body');
      const footerEl = document.getElementById('modal-footer');
      if (!titleEl || !bodyEl || !footerEl) {
        resolve(false);
        return;
      }

      const stepBeforeConfirm = editStep === 'row' ? 'row' : 'table';
      editStep = 'confirm';
      renderEditStep();

      document.getElementById('hist-no').onclick = function () {
        editStep = stepBeforeConfirm;
        if (editStep === 'row') {
          renderEditStep();
        } else {
          showEditTableView();
        }
        resolve(false);
      };
      document.getElementById('hist-yes').onclick = function () {
        showEditTableView();
        resolve(true);
      };
    });
  }

  function bindEditModalFooter() {
    const cancelBtn = document.getElementById('edit-cancel');
    const saveBtn = document.getElementById('edit-save');
    if (!cancelBtn || !saveBtn) return;

    cancelBtn.onclick = function () {
      hideModal(false);
    };
    saveBtn.onclick = async function () {
      const updateHistorical = await confirmHistoricalUpdate();
      if (editStep !== 'table') {
        showEditTableView();
      }
      showLoading(true, 'Saving categories...');
      let r;
      try {
        r = await api().save_program_categories({
          categories: editDraft,
          update_historical: updateHistorical,
        });
      } finally {
        showLoading(false);
      }
      if (r.status === 'success') {
        showAlert('Program categories saved.', 'success');
        programCategories = Object.assign({}, editDraft);
        hideModal(true);
      } else {
        showAlert(r.message || 'Save failed', 'error');
        showEditTableView();
      }
    };
  }

  window.CategoriesUI = {
    init: function (initialData) {
      categoryNames = initialData.category_names || [];
      programCategories = initialData.program_categories || {};
    },

    showCategoryPrompt: showCategoryPrompt,

    openEditModal: async function () {
      const r = await api().get_program_categories();
      if (r.status !== 'success') {
        showAlert(r.message || 'Failed to load categories', 'error');
        return;
      }
      categoryNames = r.category_names || [];
      editDraft = Object.assign({}, r.program_categories || {});
      editStep = 'table';

      const footerHtml =
        '<button type="button" class="btn" id="edit-cancel">Cancel</button>' +
        '<button type="button" class="btn" id="edit-save">Save Changes to DB</button>';

      editShell = {
        title: 'Edit Program Categories',
        footerHtml: footerHtml,
      };

      showModal({
        title: editShell.title,
        bodyHtml: renderProgramTable(),
        footerHtml: footerHtml,
        wide: true,
        onOpen: function () {
          bindEditModalEvents();
          bindEditModalFooter();
        },
      }).then(function () {
        editStep = 'table';
      });
    },
  };
})();
