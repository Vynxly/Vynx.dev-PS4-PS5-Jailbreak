(function () {
  "use strict";

  // Keep the public page user-triggered. The existing logo click starts the
  // compatibility runner; only the installed homescreen app auto-starts it.
  if (!/PlayStation 5/i.test(navigator.userAgent)) return;
  if (window.location.hostname !== "127.0.0.1" || window.location.port !== "18181") return;

  window.addEventListener("load", function () {
    window.setTimeout(function () {
      window.location.replace("./ps5-autoload/index.html");
    }, 900);
  });
})();
