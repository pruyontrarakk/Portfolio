/**
 * Corner-only ladybug runs: tl | tr | bl | br (random, no immediate repeat), ~10s crawl, then 5s hidden.
 * Expects .ladybug-crawl > .ladybug-crawl__mile and CSS data-corner + ladybug-crawl--playing.
 */
(function () {
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced.matches) return;

  var PAUSE_MS = 5000;
  var CORNERS = ["tl", "tr", "bl", "br"];

  function initZone(root) {
    var mile = root.querySelector(".ladybug-crawl__mile");
    if (!mile) return;

    var timer = null;
    var lastCorner = null;

    function pickCorner() {
      var c;
      var guard = 0;
      do {
        c = CORNERS[(Math.random() * CORNERS.length) | 0];
        guard++;
      } while (c === lastCorner && CORNERS.length > 1 && guard < 12);
      lastCorner = c;
      return c;
    }

    function playOnce() {
      mile.classList.remove("ladybug-crawl--playing");
      mile.removeAttribute("data-corner");
      void mile.offsetWidth;
      mile.setAttribute("data-corner", pickCorner());
      mile.classList.add("ladybug-crawl--playing");
    }

    function onAnimationEnd(ev) {
      if (ev.target !== mile) return;
      var name = ev.animationName || "";
      if (name.indexOf("ladybug-corner-") !== 0) return;
      mile.classList.remove("ladybug-crawl--playing");
      mile.removeAttribute("data-corner");
      if (timer) clearTimeout(timer);
      timer = setTimeout(playOnce, PAUSE_MS);
    }

    mile.addEventListener("animationend", onAnimationEnd);
    playOnce();
  }

  function boot() {
    var zones = document.querySelectorAll(".ladybug-crawl");
    for (var i = 0; i < zones.length; i++) initZone(zones[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
