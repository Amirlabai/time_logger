(function () {
  'use strict';

  let categoryNames = [];
  let programCategories = {};
  let editDraft = {};
  let promptOpen = false;

  function api() {
    return window.pywebview.api;
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  function showCategoryPrompt(data) {
    if (!data || !data.program || promptOpen) return;
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
      '<div class="form-row"><label>Available categories</label>' +
      '<select id="prompt-category-select"><option value="">-- select --</option>' +
      options +
      '</select></div>' +
      '<div class="form-row"><label>Or enter new category</label>' +
      '<input type="text" id="prompt-category-new" placeholder="New category"></div>';

    const footerHtml =
      '<button type="button" class="btn" id="prompt-dismiss">Use Misc</button>' +
      '<button type="button" class="btn" id="prompt-submit">Submit</button>';

    showModal({
      title: 'Categorize: ' + program,
      bodyHtml: bodyHtml,
      footerHtml: footerHtml,
      closable: false,
    }).then(function () {
      promptOpen = false;
    });

    setTimeout(function () {
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
      document.getElementById('prompt-category-new').focus();
    }, 0);
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
      '<hr style="border-color:#444;margin:12px 0">' +
      '<p><em>Add or update program in list</em></p>' +
      '<div class="form-row"><label>Program name</label>' +
      '<input type="text" id="new-program-name"></div>' +
      '<div class="form-row"><label>Category</label>' +
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

  function restoreEditModalShell(savedTitle, savedFooterHtml) {
    const titleEl = document.getElementById('modal-title');
    const footerEl = document.getElementById('modal-footer');
    if (titleEl) titleEl.textContent = savedTitle;
    if (footerEl) footerEl.innerHTML = savedFooterHtml;
    refreshEditModalBody();
    bindEditModalFooter();
  }

  function editRowCategory(program, current) {
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');
    const footerEl = document.getElementById('modal-footer');
    if (!titleEl || !bodyEl || !footerEl) return;

    const savedTitle = titleEl.textContent;
    const savedFooterHtml = footerEl.innerHTML;

    const options = categoryNames
      .map(function (c) {
        const sel = c === current ? ' selected' : '';
        return '<option value="' + escapeHtml(c) + '"' + sel + '>' + escapeHtml(c) + '</option>';
      })
      .join('');

    titleEl.textContent = 'Set Category for: ' + program;
    bodyEl.innerHTML =
      '<p>Program: <strong>' +
      escapeHtml(program) +
      '</strong></p>' +
      '<div class="form-row"><label>Select category</label>' +
      '<select id="edit-row-select">' +
      options +
      '</select></div>' +
      '<div class="form-row"><label>Or new category</label>' +
      '<input type="text" id="edit-row-new"></div>';
    footerEl.innerHTML =
      '<button type="button" class="btn" id="edit-row-cancel">Cancel</button>' +
      '<button type="button" class="btn" id="edit-row-ok">OK</button>';

    document.getElementById('edit-row-cancel').onclick = function () {
      restoreEditModalShell(savedTitle, savedFooterHtml);
    };
    document.getElementById('edit-row-ok').onclick = function () {
      const entered = document.getElementById('edit-row-new').value.trim();
      const selected = document.getElementById('edit-row-select').value;
      let newCat = current;
      if (entered) {
        newCat = entered.replace(/\b\w/g, function (l) {
          return l.toUpperCase();
        });
        if (categoryNames.indexOf(newCat) === -1) categoryNames.push(newCat);
      } else if (selected) {
        newCat = selected;
      }
      editDraft[program] = newCat;
      restoreEditModalShell(savedTitle, savedFooterHtml);
    };
  }

  function bindEditModalEvents() {
    document.querySelectorAll('.btn-edit-row').forEach(function (btn) {
      btn.onclick = function () {
        const tr = btn.closest('tr');
        const program = tr.getAttribute('data-program');
        const cat = editDraft[program] || 'Misc';
        editRowCategory(program, cat);
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
        refreshEditModalBody();
      };
    }
  }

  function refreshEditModalBody() {
    const bodyEl = document.getElementById('modal-body');
    if (!bodyEl) return;
    bodyEl.innerHTML = renderProgramTable();
    bindEditModalEvents();
  }

  function bindEditModalFooter() {
    const cancelBtn = document.getElementById('edit-cancel');
    const saveBtn = document.getElementById('edit-save');
    if (!cancelBtn || !saveBtn) return;

    cancelBtn.onclick = function () {
      hideModal(false);
    };
    saveBtn.onclick = async function () {
      const updateHistorical = window.confirm(
        'Update historical log entries for changed programs?\n(This might take a moment and cannot be undone easily)'
      );
      const r = await api().save_program_categories({
        categories: editDraft,
        update_historical: updateHistorical,
      });
      if (r.status === 'success') {
        showAlert('Program categories saved.', 'success');
        programCategories = Object.assign({}, editDraft);
        hideModal(true);
      } else {
        showAlert(r.message || 'Save failed', 'error');
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

      const footerHtml =
        '<button type="button" class="btn" id="edit-cancel">Cancel</button>' +
        '<button type="button" class="btn" id="edit-save">Save Changes to DB</button>';

      showModal({
        title: 'Edit Program Categories',
        bodyHtml: renderProgramTable(),
        footerHtml: footerHtml,
        wide: true,
      }).then(function () {});

      setTimeout(function () {
        bindEditModalEvents();
        bindEditModalFooter();
      }, 0);
    },
  };
})();
