(function () {
  function openHash() {
    var id = location.hash.replace(/^#/, "");
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.tagName === "DETAILS") el.open = true;
  }
  var menu = document.querySelector(".nav-menu");
  var summary = menu && menu.querySelector("summary");
  var mq = window.matchMedia("(max-width: 720px)");
  function syncExpanded() {
    if (!summary || !menu) return;
    summary.setAttribute("aria-expanded", menu.open ? "true" : "false");
  }
  function adaptNav() {
    if (!menu) return;
    if (mq.matches) {
      menu.removeAttribute("open");
    } else {
      menu.setAttribute("open", "");
    }
    syncExpanded();
  }
  function closeNav() {
    if (menu && mq.matches) menu.removeAttribute("open");
    syncExpanded();
  }
  openHash();
  window.addEventListener("hashchange", openHash);
  if (mq.addEventListener) mq.addEventListener("change", adaptNav);
  else mq.addListener(adaptNav);
  adaptNav();
  if (menu) menu.addEventListener("toggle", syncExpanded);
  document.querySelectorAll(".site-nav a").forEach(function (a) {
    a.addEventListener("click", closeNav);
  });
})();
