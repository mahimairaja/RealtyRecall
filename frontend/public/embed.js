/*
 * RealtyRecall embeddable call widget.
 *
 * A realtor drops this on their own site:
 *   <script src="https://<realtyrecall-host>/embed.js" data-org="org_xxx" async></script>
 *
 * It adds a floating "Talk to us" button that opens the buyer call widget in an overlay iframe,
 * scoped to that realtor's org (so the assistant knows their listings). No dependencies; the
 * base URL is derived from this script's own src, so it works on any domain.
 */
(function () {
  "use strict";

  var script =
    document.currentScript || document.querySelector("script[data-org]");
  if (!script) return;

  var org = script.getAttribute("data-org");
  if (!org) {
    console.error("[RealtyRecall] embed.js: missing data-org attribute");
    return;
  }
  var label = script.getAttribute("data-label") || "Talk to us";
  var base = new URL(script.src).origin;
  var url = base + "/embed/" + encodeURIComponent(org);

  function ready(fn) {
    if (document.body) fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var overlay = null;

    function openWidget() {
      if (overlay) {
        overlay.style.display = "block";
        return;
      }
      overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;z-index:2147483001;background:rgba(0,0,0,.4);";
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) overlay.style.display = "none";
      });

      var panel = document.createElement("div");
      panel.style.cssText =
        "position:fixed;bottom:20px;right:20px;width:min(420px,calc(100vw - 40px));" +
        "height:min(640px,calc(100vh - 40px));background:#fff;border-radius:16px;" +
        "overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.35);";

      var iframe = document.createElement("iframe");
      iframe.src = url;
      iframe.allow = "microphone";
      iframe.title = "Talk to our assistant";
      iframe.style.cssText = "width:100%;height:100%;border:0;display:block;";

      var close = document.createElement("button");
      close.setAttribute("aria-label", "Close");
      close.textContent = "×";
      close.style.cssText =
        "position:absolute;top:8px;right:10px;z-index:1;background:rgba(0,0,0,.5);" +
        "color:#fff;border:0;border-radius:999px;width:28px;height:28px;" +
        "font-size:18px;line-height:1;cursor:pointer;";
      close.addEventListener("click", function () {
        overlay.style.display = "none";
      });

      panel.appendChild(iframe);
      panel.appendChild(close);
      overlay.appendChild(panel);
      document.body.appendChild(overlay);
    }

    var button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("aria-label", label);
    button.style.cssText =
      "position:fixed;bottom:20px;right:20px;z-index:2147483000;background:#0e2338;" +
      "color:#fff;border:0;border-radius:999px;padding:12px 22px;" +
      "font:600 15px system-ui,-apple-system,sans-serif;" +
      "box-shadow:0 8px 24px rgba(14,35,56,.35);cursor:pointer;";
    button.addEventListener("click", openWidget);
    document.body.appendChild(button);
  });
})();
