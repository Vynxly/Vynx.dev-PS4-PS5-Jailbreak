(function () {
  "use strict";

  // The public page is user-triggered: its logo click calls jailbreak().
  // Only the installed homescreen app should start the chain automatically.
  if (!/PlayStation 5/i.test(navigator.userAgent)) return;
  if (window.location.hostname !== "127.0.0.1" || window.location.port !== "18181") return;

  window.addEventListener("load", function () {
    window.setTimeout(function () {
      window.location.replace("./ps5-autoload/index.html");
    }, 900);
  });
})();
