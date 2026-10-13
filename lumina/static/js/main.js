/* =====================================================================
   LUMINA E-LIBRARY  -  TINY PUBLIC SCRIPT  (js/main.js)
   ---------------------------------------------------------------------
   The site is built with HTML + CSS first. This file adds only five
   small "nice to have" behaviours. If JavaScript is switched off, every
   page still works - these just make a few things more comfortable.

     1. Show / hide password            (login, register, change password)
     2. "Passwords must match" check    (register, reset, change password)
     3. Live book filter                (books.html)
     4. Reader text-size toggle         (read.html)
     5. Loan history filter             (my-loans.html)

   NOTE: the mobile menu is NOT here - it is pure CSS (checkbox trick).
   ===================================================================== */

/* ---------- 1. SHOW / HIDE PASSWORD ----------
   Any <button data-toggle-pw="inputId"> flips that input between
   type="password" and type="text". */
document.querySelectorAll('[data-toggle-pw]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var input = document.getElementById(btn.dataset.togglePw);   // find the matching field
    var hidden = input.type === 'password';                      // is it currently hidden?
    input.type = hidden ? 'text' : 'password';                   // swap the type
    btn.textContent = hidden ? 'Hide' : 'Show';                  // swap the label
  });
});

/* ---------- 2. PASSWORDS MUST MATCH ----------
   Any <form data-match> that has #password and #confirm fields is checked
   before it is sent. HTML cannot compare two fields on its own, so this
   is the one small job we give to JavaScript. */
document.querySelectorAll('form[data-match]').forEach(function (form) {
  form.addEventListener('submit', function (e) {
    var pw = form.querySelector('#password, #new-password');
    var cf = form.querySelector('#confirm');
    var msg = form.querySelector('.match-error');
    if (pw && cf && pw.value !== cf.value) {
      e.preventDefault();            // stop the form from being sent
      if (msg) { msg.hidden = false; }   // reveal the red message
      cf.focus();
    }
  });
});

/* ---------- 3. LIVE BOOK FILTER ----------
   On books.html each card carries data-title / data-author / data-publisher /
   data-category / data-type. As the visitor types or changes a dropdown we
   simply hide the cards that do not match. (The real search will be done
   by the backend - this is just a friendly preview.) */
var filterForm = document.getElementById('book-filter');
if (filterForm) {
  var cards = document.querySelectorAll('.book-card');
  var applyFilter = function () {
    var q    = filterForm.elements['q'].value.toLowerCase();       // typed words
    var by   = filterForm.elements['by'].value;                    // all/title/author/publisher
    var cat  = filterForm.elements['category'].value;              // category slug or ''
    var type = filterForm.elements['type'].value;                  // Book / Video or ''
    cards.forEach(function (c) {
      var hay = by === 'all'
        ? (c.dataset.title + ' ' + c.dataset.author + ' ' + c.dataset.publisher).toLowerCase()
        : (c.dataset[by] || '').toLowerCase();
      var ok = hay.indexOf(q) > -1 &&
               (!cat  || c.dataset.category === cat) &&
               (!type || c.dataset.type === type);
      c.style.display = ok ? '' : 'none';                          // show or hide the card
    });
  };
  filterForm.addEventListener('input', applyFilter);
  filterForm.addEventListener('change', applyFilter);
}

/* ---------- 4. READER TEXT-SIZE TOGGLE ----------
   Adds / removes the .large class on the reading page. CSS does the rest. */
var sizeBtn = document.getElementById('text-size');
if (sizeBtn) {
  sizeBtn.addEventListener('click', function () {
    document.querySelector('.reader-page').classList.toggle('large');
  });
}

/* ---------- 5. LOAN HISTORY FILTER ----------
   On my-loans.html each table row carries data-status="issued|overdue|returned".
   Typing in #loan-search or changing #loan-status simply hides the rows that
   do not match. Without JavaScript the full history is still shown. */
var loanTable = document.getElementById('loan-table');
if (loanTable) {
  var loanSearch = document.getElementById('loan-search');
  var loanStatus = document.getElementById('loan-status');
  var loanEmpty  = document.getElementById('loan-empty');
  var filterLoans = function () {
    var q = loanSearch.value.toLowerCase().trim();                  // typed words
    var visible = 0;
    loanTable.querySelectorAll('tbody tr').forEach(function (row) {
      var okText   = row.textContent.toLowerCase().indexOf(q) > -1;  // text match
      var okStatus = loanStatus.value === 'all' || row.dataset.status === loanStatus.value;
      row.hidden = !(okText && okStatus);                            // hide or show the row
      if (!row.hidden) { visible++; }
    });
    loanEmpty.hidden = visible > 0;                                  // "no records" message
  };
  loanSearch.addEventListener('input', filterLoans);
  loanStatus.addEventListener('change', filterLoans);
}
