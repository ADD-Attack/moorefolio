// Chess Coach — Plans page (Ticket 006 Phase 3; redeem wired Phase 4).
// Standalone script: price toggle, mini demo board, checkout, test-code redeem.
// DOM surface is kept small so the page suite can load this file headlessly.
(function () {
  "use strict";

  var CHECKOUT_URL = "https://abraham-1.tail629694.ts.net/v1/billing/checkout";
  var ACCOUNT_KEYS = [
    "chessCoachAccount.you",
    "chessCoachAccount.ben",
    "chessCoachAccount.test",
    "chessCoachAccount.kids",
    "chessCoachAccount.beginnertest"
  ];

  var CREATE_ACCOUNT_NOTE = "Create your account first — open a coach page and use Options → Account.";
  var BILLING_NOT_OPEN_NOTE = "Billing isn't open yet — plans launch soon. Your beta access keeps working.";
  var ERROR_NOTE = "Something went wrong — try again in a moment.";
  var REDEEM_URL = "https://abraham-1.tail629694.ts.net/v1/redeem";
  var REDEEM_OK_NOTE = "Test code accepted — you're in for 7 days.";
  var REDEEM_BAD_NOTE = "That code wasn't recognized — check it and try again.";
  var REDEEM_EMPTY_NOTE = "Enter your test code first.";
  var REDEEM_SLOW_NOTE = "Too many tries — wait a bit and try again.";

  var annual = false;

  function el(id) {
    if (typeof document === "undefined" || !document || typeof document.getElementById !== "function") return null;
    try { return document.getElementById(id); } catch (e) { return null; }
  }
  function setText(id, text) {
    var node = el(id);
    if (node) node.textContent = text;
  }

  // ---- mini demo board ----
  var START_BOARD = [
    "♜","♞","♝","♛","♚","♝","♞","♜",
    "♟","♟","♟","♟","♟","♟","♟","♟",
    "","","","","","","","",
    "","","","","","","","",
    "","","","","","","","",
    "","","","","","","","",
    "♙","♙","♙","♙","♙","♙","♙","♙",
    "♖","♘","♗","♕","♔","♗","♘","♖"
  ];
  // Square indices run a8=0 .. h1=63.
  var STEPS = [
    { from: 52, to: 36, line: "Pawn to the center to start." },
    { from: 12, to: 28, line: "I'm putting a pawn in the center too." },
    { from: 62, to: 45, line: "Knight out, eyeing that pawn." },
    { from: 1, to: 18, line: "My knight guards it." },
    { from: 61, to: 34, line: "Bishop aims at the middle." },
    { from: 6, to: 21, line: "And my knight comes out too." }
  ];
  var board = START_BOARD.slice();
  var stepIndex = 0;

  function renderBoard() {
    for (var i = 0; i < 64; i++) setText("demoSq" + i, board[i]);
  }
  function stepDemo() {
    if (stepIndex >= STEPS.length) {
      board = START_BOARD.slice();
      stepIndex = 0;
      renderBoard();
      setText("demoLine", "Watch a short game.");
      return;
    }
    var step = STEPS[stepIndex];
    board[step.to] = board[step.from];
    board[step.from] = "";
    stepIndex++;
    renderBoard();
    setText("demoLine", step.line);
  }

  // ---- monthly / annual toggle ----
  function markToggle(node, on) {
    if (!node || !node.classList) return;
    try {
      if (typeof node.classList.toggle === "function") node.classList.toggle("active", !!on);
      else if (on && typeof node.classList.add === "function") node.classList.add("active");
      else if (!on && typeof node.classList.remove === "function") node.classList.remove("active");
    } catch (e) { /* class styling is cosmetic */ }
  }
  function setAnnual(value) {
    annual = !!value;
    setText("coachPrice", annual ? "$120" : "$12");
    setText("coachSuffix", annual ? "/yr" : "/mo");
    setText("proPrice", annual ? "$290" : "$29");
    setText("proSuffix", annual ? "/yr" : "/mo");
    markToggle(el("toggleMonthly"), !annual);
    markToggle(el("toggleAnnual"), annual);
  }

  // ---- account token + checkout ----
  function findToken() {
    if (typeof sessionStorage === "undefined" || !sessionStorage || typeof sessionStorage.getItem !== "function") return null;
    for (var i = 0; i < ACCOUNT_KEYS.length; i++) {
      var raw = null;
      try { raw = sessionStorage.getItem(ACCOUNT_KEYS[i]); } catch (e) { raw = null; }
      if (!raw) continue;
      try {
        var parsed = JSON.parse(raw);
        if (parsed && parsed.token) return parsed.token;
      } catch (e) { /* keep looking at the next key */ }
    }
    return null;
  }

  function showBillingNote(text, withCoachLink) {
    var note = el("billingNote");
    if (!note) return;
    if (withCoachLink) {
      note.innerHTML = text + ' <a href="/coach-you/">Open a coach page</a>';
    } else {
      note.textContent = text;
    }
  }

  function checkout(plan) {
    var token = findToken();
    if (!token) {
      showBillingNote(CREATE_ACCOUNT_NOTE, true);
      return Promise.resolve(false);
    }
    var interval = plan === "byok_weekly" ? "weekly" : (annual ? "annual" : "monthly");
    if (typeof fetch !== "function") {
      showBillingNote(ERROR_NOTE, false);
      return Promise.resolve(false);
    }
    var request;
    try {
      request = fetch(CHECKOUT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ plan: plan, interval: interval })
      });
    } catch (e) {
      showBillingNote(ERROR_NOTE, false);
      return Promise.resolve(false);
    }
    return Promise.resolve(request).then(function (res) {
      var status = res && typeof res.status === "number" ? res.status : 0;
      var readJson = res && typeof res.json === "function"
        ? Promise.resolve(res.json()).catch(function () { return null; })
        : Promise.resolve(null);
      return readJson.then(function (data) {
        if (data && data.url) {
          if (typeof location !== "undefined" && location) location.href = data.url;
          return true;
        }
        if (status === 503 || (data && data.billing_configured === false)) {
          showBillingNote(BILLING_NOT_OPEN_NOTE, false);
          return false;
        }
        showBillingNote(ERROR_NOTE, false);
        return false;
      });
    }).catch(function () {
      showBillingNote(ERROR_NOTE, false);
      return false;
    });
  }

  function planOf(button) {
    if (!button) return null;
    if (button.dataset && button.dataset.plan) return button.dataset.plan;
    if (typeof button.getAttribute === "function") return button.getAttribute("data-plan");
    return null;
  }

  // ---- wiring (all guarded, so the file also loads headlessly) ----
  var monthlyBtn = el("toggleMonthly");
  if (monthlyBtn && typeof monthlyBtn.addEventListener === "function") {
    monthlyBtn.addEventListener("click", function () { setAnnual(false); });
  }
  var annualBtn = el("toggleAnnual");
  if (annualBtn && typeof annualBtn.addEventListener === "function") {
    annualBtn.addEventListener("click", function () { setAnnual(true); });
  }

  if (typeof document !== "undefined" && document && typeof document.querySelectorAll === "function") {
    var planButtons = document.querySelectorAll("[data-plan]");
    if (planButtons) {
      for (var i = 0; i < planButtons.length; i++) {
        (function (button) {
          if (button && typeof button.addEventListener === "function") {
            button.addEventListener("click", function () { return checkout(planOf(button)); });
          }
        })(planButtons[i]);
      }
    }
  }

  // ---- test-code redemption (Phase 4) ----
  // A redeemed code returns a guest session. The blob is stored
  // under EVERY coach page's account key, so whichever coach page
  // the guest opens next (same tab) restores it from sessionStorage
  // and the banner + claim flow are waiting there.
  function redeem() {
    var input = el("testCodeInput");
    var code = input && typeof input.value === "string" ? input.value.trim() : "";
    if (!code) { setText("redeemNote", REDEEM_EMPTY_NOTE); return Promise.resolve(false); }
    if (typeof fetch !== "function") { setText("redeemNote", ERROR_NOTE); return Promise.resolve(false); }
    setText("redeemNote", "Checking your code…");
    var request;
    try {
      request = fetch(REDEEM_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code })
      });
    } catch (e) {
      setText("redeemNote", ERROR_NOTE);
      return Promise.resolve(false);
    }
    return Promise.resolve(request).then(function (res) {
      var status = res && typeof res.status === "number" ? res.status : 0;
      var readJson = res && typeof res.json === "function"
        ? Promise.resolve(res.json()).catch(function () { return null; })
        : Promise.resolve(null);
      return readJson.then(function (data) {
        if (status === 200 && data && data.token && data.account) {
          var blob = JSON.stringify({ token: data.token, exp: data.exp,
            email: data.account.email || null, plan: data.account.plan,
            guest: !!data.account.guest,
            guest_days_left: typeof data.account.guest_days_left === "number" ? data.account.guest_days_left : null,
            guest_expires_at: data.account.guest_expires_at || null });
          if (typeof sessionStorage !== "undefined" && sessionStorage && typeof sessionStorage.setItem === "function") {
            for (var i = 0; i < ACCOUNT_KEYS.length; i++) {
              try { sessionStorage.setItem(ACCOUNT_KEYS[i], blob); } catch (e) { /* one key failing must not lose the rest */ }
            }
          }
          var note = el("redeemNote");
          if (note) note.innerHTML = REDEEM_OK_NOTE + ' <a href="/coach-you/">Open the coach and play</a>';
          return true;
        }
        if (status === 401) { setText("redeemNote", REDEEM_BAD_NOTE); return false; }
        if (status === 429) { setText("redeemNote", REDEEM_SLOW_NOTE); return false; }
        setText("redeemNote", ERROR_NOTE);
        return false;
      });
    }).catch(function () {
      setText("redeemNote", ERROR_NOTE);
      return false;
    });
  }

  var redeemBtn = el("redeemBtn");
  if (redeemBtn && typeof redeemBtn.addEventListener === "function") {
    redeemBtn.addEventListener("click", function () { return redeem(); });
  }

  setAnnual(false);
  renderBoard();
  if (typeof setInterval === "function") {
    try { setInterval(stepDemo, 1800); } catch (e) { /* demo loop is decorative */ }
  }
})();
