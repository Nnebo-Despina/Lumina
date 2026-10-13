/* =====================================================================
   LUMINA E-LIBRARY  -  TINY ADMIN SCRIPT  (admin/admin.js)
   ---------------------------------------------------------------------
   The original template rebuilt whole pages with JavaScript. Here the
   pages are real HTML and CSS; this file only adds four small helpers:

     1. Confirm before deleting / returning -> any element with data-confirm="..."
     2. Filter a table while typing          -> <input data-filter="#tableId">
        (+ optional status dropdown)         -> <select data-status-filter="#tableId">
     3. Print button                         -> any element with data-print
     4. Issue-form dates                     -> <form data-dates> (issue-form.html)

   Modals, menus, toggle switches and the sidebar need NO JavaScript.
   ===================================================================== */

/* ---------- 1. CONFIRM BEFORE DELETE / RETURN ----------
   Buttons like  <button data-confirm="Delete this category?">  ask first.
   If the admin clicks "Cancel", we stop the form from submitting. */
document.querySelectorAll('[data-confirm]').forEach(function (el) {
  el.addEventListener('click', function (e) {
    if (!window.confirm(el.dataset.confirm)) { e.preventDefault(); }
  });
});

/* ---------- 2. LIVE TABLE FILTER (text + optional status) ----------
   A text box (data-filter) and/or a dropdown (data-status-filter) point at a
   table by its id. A row stays visible only if it matches BOTH.
   Rows carry data-status="issued|overdue|returned" for the dropdown.
   If an element with id "<tableId>-empty" exists it is shown when no rows match. */
function applyTableFilter(tableSel) {
  var box  = document.querySelector('[data-filter="' + tableSel + '"]');
  var drop = document.querySelector('[data-status-filter="' + tableSel + '"]');
  var q = box ? box.value.toLowerCase().trim() : '';          // typed words
  var st = drop ? drop.value : 'all';                          // chosen status
  var visible = 0;
  document.querySelectorAll(tableSel + ' tbody tr').forEach(function (row) {
    var okText = row.textContent.toLowerCase().indexOf(q) > -1;
    var okStatus = st === 'all' || row.dataset.status === st;
    row.hidden = !(okText && okStatus);                        // hide or show the row
    if (!row.hidden) { visible++; }
  });
  var empty = document.getElementById(tableSel.replace('#', '') + '-empty');
  if (empty) { empty.hidden = visible > 0; }                   // "no records" message
}
document.querySelectorAll('[data-filter]').forEach(function (input) {
  input.addEventListener('input', function () { applyTableFilter(input.dataset.filter); });
});
document.querySelectorAll('[data-status-filter]').forEach(function (sel) {
  sel.addEventListener('change', function () { applyTableFilter(sel.dataset.statusFilter); });
});

/* ---------- 3. PRINT BUTTON ----------
   Used on the Reports page. Print styles in style.css hide the menus. */
document.querySelectorAll('[data-print]').forEach(function (btn) {
  btn.addEventListener('click', function () { window.print(); });
});

/* ---------- 4. ISSUE-FORM DATES ----------
   Pre-fills today as the issue date and +14 days as the due date, stops
   future issue dates, and refuses a due date that is not after the issue date.
   (The backend must check this again - browser checks are only a convenience.) */
var dateForm = document.querySelector('form[data-dates]');
if (dateForm) {
  var issue = dateForm.querySelector('#issue_date');
  var due   = dateForm.querySelector('#due_date');
  // turn a Date into "YYYY-MM-DD" using LOCAL time (toISOString would use UTC)
  var iso = function (d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  };
  // add n days to a "YYYY-MM-DD" string
  var addDays = function (str, n) {
    var p = str.split('-');
    return iso(new Date(+p[0], +p[1] - 1, +p[2] + n));
  };
  var checkDates = function () {
    // empty message = valid; text = the browser shows it and blocks submit
    due.setCustomValidity(due.value && due.value <= issue.value ? 'Due date must be after the issue date.' : '');
  };
  if (!issue.value) { issue.value = iso(new Date()); }          // default: today
  issue.max = iso(new Date());                                  // cannot issue in the future
  if (!due.value)   { due.value = addDays(issue.value, 14); }   // default: 14-day loan
  due.min = addDays(issue.value, 1);
  issue.addEventListener('change', function () {
    due.min = addDays(issue.value, 1);                          // due date must come later
    due.value = addDays(issue.value, 14);                       // re-suggest 14 days
    checkDates();
  });
  due.addEventListener('input', checkDates);
  checkDates();
}
