/* Decant surface — vanilla JS, no framework. */

(function () {
  "use strict";

  // --- DOM refs ---
  var urlForm = document.getElementById("url-form");
  var urlInput = document.getElementById("url-input");
  var dropZone = document.getElementById("drop-zone");
  var fileInput = document.getElementById("file-input");
  var inputZone = document.getElementById("input-zone");
  var outputSection = document.getElementById("output");
  var outputFrame = document.getElementById("output-frame");
  var errorContainer = document.getElementById("error");
  var errorMessage = document.getElementById("error-message");
  var errorHint = document.getElementById("error-hint");
  var convertingStatus = document.getElementById("converting");
  var toolbarContainer = document.getElementById("toolbar-container");
  var fontSizeSlider = document.getElementById("font-size-slider");
  var resetBtn = document.getElementById("reset-btn");
  var feedbackWidget = document.getElementById("feedback-widget");
  var feedbackUp = document.getElementById("feedback-up");
  var feedbackDown = document.getElementById("feedback-down");
  var feedbackExpand = document.getElementById("feedback-expand");
  var feedbackText = document.getElementById("feedback-text");
  var feedbackSubmit = document.getElementById("feedback-submit");
  var urlClear = document.getElementById("url-clear");
  var tryDemoBtn = document.getElementById("try-demo-btn");

  // --- Settings state ---
  var DEFAULTS = {
    fontSize: 2,
    theme: "light",
    font: "sans",
    spacing: "standard",
    width: "medium"
  };

  var FONT_SIZE_MULTIPLIERS = [0.7, 0.85, 1.0, 1.25, 1.5];

  var THEMES = {
    light:    { bg: "#fafaf7", text: "#333",    link: "#1856a8", visited: "#694598", notice: { bg: "#f0f0e8", border: "#b0a870", text: "#555555" }, demo: { bg: "#eef4fa", border: "#7aabe0", text: "#2a4a6a", btnBg: "#7aabe0", btnText: "#fff" } },
    cream:    { bg: "#f5f0e8", text: "#333",    link: "#3a6ea5", visited: "#8b5e83", notice: { bg: "#e8dfca", border: "#a08860", text: "#5b4636" }, demo: { bg: "#eae4d8", border: "#8a7a60", text: "#5b4636", btnBg: "#8a7a60", btnText: "#fff" } },
    dark:     { bg: "#1e1e1e", text: "#e0e0e0", link: "#6db3f2", visited: "#c4a4ff", notice: { bg: "rgb(55, 54, 66)", border: "rgb(140, 140, 160)", text: "rgb(200, 200, 210)" }, demo: { bg: "rgb(40, 50, 65)", border: "rgb(100, 150, 200)", text: "rgb(200, 210, 225)", btnBg: "rgb(100, 150, 200)", btnText: "#1e1e1e" } },
    contrast: { bg: "#1a1a1a", text: "#ffd700", link: "#00e5ff", visited: "#ff80ab", notice: { bg: "#000000", border: "#ffee32", text: "#ffffff" }, demo: { bg: "#000000", border: "#00e5ff", text: "#ffffff", btnBg: "#00e5ff", btnText: "#000" } }
  };

  var WIDTH_VALUES = { narrow: "38em", medium: "48em", wide: "60em" };
  var WIDTH_LABELS = { narrow: "Narrow", medium: "Medium", wide: "Wide" };

  var SPACING_VALUES = {
    standard: null,
    loose: { letterSpacing: "0.08em", wordSpacing: "0.3em", lineHeight: "1.8" },
    veryloose: { letterSpacing: "0.14em", wordSpacing: "0.45em", lineHeight: "2.1" }
  };

  var SPACING_LABELS = { standard: "Standard", loose: "Loose", veryloose: "Very Loose" };

  var settings = loadSettings();
  var currentSourceUrl = "";
  var currentHtml = "";
  var isDemoConversion = false;
  var dropZoneDefault = dropZone.querySelector("p").textContent;

  // --- localStorage ---

  function loadSettings() {
    try {
      var stored = localStorage.getItem("decant_settings");
      if (stored) {
        var parsed = JSON.parse(stored);
        return {
          fontSize: parsed.fontSize !== undefined ? parsed.fontSize : DEFAULTS.fontSize,
          theme: parsed.theme || DEFAULTS.theme,
          font: parsed.font || DEFAULTS.font,
          spacing: (parsed.spacing === true) ? "loose" : (parsed.spacing === false) ? "standard" : (parsed.spacing || DEFAULTS.spacing),
          width: parsed.width || DEFAULTS.width
        };
      }
    } catch (e) { /* ignore */ }
    return JSON.parse(JSON.stringify(DEFAULTS));
  }

  function saveSettings() {
    try {
      localStorage.setItem("decant_settings", JSON.stringify(settings));
    } catch (e) { /* ignore */ }
  }

  // --- UI state helpers ---

  function showError(message, hint) {
    errorMessage.textContent = message;
    errorHint.textContent = hint || "";
    errorContainer.classList.remove("hidden");
    outputSection.classList.add("hidden");
    convertingStatus.classList.add("hidden");
  }

  function hideError() {
    errorContainer.classList.add("hidden");
  }

  function showLoading() {
    hideError();
    outputSection.classList.add("hidden");
    convertingStatus.classList.remove("hidden");
  }

  function showResult(html, sourceUrl) {
    hideError();
    convertingStatus.classList.add("hidden");
    outputSection.classList.remove("hidden");

    currentHtml = html;
    currentSourceUrl = sourceUrl;

    // Show action-only toolbar buttons (url-only ones only for URL conversions)
    document.querySelectorAll(".action-only").forEach(function (el) {
      if (el.classList.contains("url-only")) {
        el.classList.toggle("hidden", !sourceUrl);
      } else {
        el.classList.remove("hidden");
      }
    });

    // Reset feedback widget
    feedbackUp.classList.remove("active");
    feedbackDown.classList.remove("active");
    feedbackExpand.classList.add("hidden");
    feedbackText.value = "";

    applyToIframe();
  }

  function handleErrorResponse(resp, data) {
    var message = (data && data.message) || "Conversion failed.";
    var hint = "";
    var status = resp.status;

    if (status === 429) {
      hint = "You can try again shortly.";
    } else if (status === 500) {
      hint = "If this keeps happening, the page may not be compatible.";
    }

    showError(message, hint);
  }

  // --- CSS injection into iframe ---

  function buildOverrideCSS() {
    var css = [];
    var theme = THEMES[settings.theme] || THEMES.light;
    var multiplier = FONT_SIZE_MULTIPLIERS[settings.fontSize] || 1.0;

    // Theme colors
    css.push("body { background-color: " + theme.bg + " !important; color: " + theme.text + " !important; }");
    css.push("a { color: " + theme.link + " !important; }");
    css.push("a:visited { color: " + theme.visited + " !important; }");

    // Font size (zoom scales everything proportionally)
    if (multiplier !== 1.0) {
      css.push("body { zoom: " + multiplier + " !important; }");
    }

    // Font family
    if (settings.font === "opendyslexic") {
      css.push("body { font-family: 'OpenDyslexic', Arial, Verdana, sans-serif !important; }");
    } else if (settings.font === "serif") {
      css.push("body { font-family: Georgia, 'Times New Roman', serif !important; }");
    } else {
      css.push("body { font-family: Arial, Verdana, 'Segoe UI', sans-serif !important; }");
    }

    // Text spacing
    var sv = SPACING_VALUES[settings.spacing];
    if (sv) {
      css.push("body { letter-spacing: " + sv.letterSpacing + " !important; word-spacing: " + sv.wordSpacing + " !important; line-height: " + sv.lineHeight + " !important; }");
    }

    // Content width
    var maxW = WIDTH_VALUES[settings.width] || WIDTH_VALUES.medium;
    if (multiplier !== 1.0) {
      css.push(".container { max-width: calc(" + maxW + " / " + multiplier + ") !important; }");
    } else {
      css.push(".container { max-width: " + maxW + " !important; }");
    }

    css.push(".container { padding-top: 0.5rem !important; }");
    css.push(".container > :first-child { margin-top: 0 !important; }");

    // Notice banner theme colors
    if (theme.notice) {
      css.push(".decant-notice { background-color: " + theme.notice.bg + " !important; border-left-color: " + theme.notice.border + " !important; color: " + theme.notice.text + " !important; }");
    }

    // Demo welcome banner theme colors
    if (theme.demo) {
      css.push(".decant-demo-banner { background-color: " + theme.demo.bg + " !important; border-left-color: " + theme.demo.border + " !important; color: " + theme.demo.text + " !important; }");
      css.push(".decant-demo-banner button { background-color: " + theme.demo.btnBg + " !important; color: " + theme.demo.btnText + " !important; }");
    }

    return css.join("\n");
  }

  // Map from THEMES key to body class name
  var THEME_BODY_CLASS = {
    light: "",
    cream: "sepia",
    dark: "dark",
    contrast: "contrast"
  };

  function applyOuterTheme() {
    // Remove all theme classes
    document.body.classList.remove("sepia", "dark", "contrast");
    // Add the new one (light has no class)
    var cls = THEME_BODY_CLASS[settings.theme];
    if (cls) document.body.classList.add(cls);
  }

  var DEMO_BANNER_HTML =
    '<div class="decant-demo-banner" style="' +
      'font-family: Arial, Verdana, sans-serif; font-size: 14px; line-height: 1.6; ' +
      'padding: 16px 20px; margin: 0 auto 16px; max-width: 48em; ' +
      'border-left: 4px solid; border-radius: 4px;">' +
      '<p style="margin: 0 0 8px;">You\u2019re looking at the demo web page, cleaned up by Decant. ' +
      'The original is full of ads, pop-ups, and clutter \u2014 click ' +
      '<strong>View Original</strong> in the toolbar to see how bad it is.</p>' +
      '<p style="margin: 0 0 12px;">When you\u2019re done, come back to ' +
      '<strong>Help &gt; Getting Started</strong> to finish the guide.</p>' +
      '<button id="decant-demo-dismiss" style="' +
        'border: none; border-radius: 4px; padding: 5px 14px; ' +
        'font-size: 13px; font-weight: 600; cursor: pointer;">' +
        'Got it</button>' +
    '</div>';

  function applyToIframe() {
    if (!currentHtml) return;

    applyOuterTheme();

    var overrideCSS = buildOverrideCSS();
    var styleTag = '<style id="decant-override">' + overrideCSS + '</style>';

    // Insert override style just before </head>
    var injected = currentHtml;
    if (injected.indexOf("</head>") !== -1) {
      injected = injected.replace("</head>", styleTag + "</head>");
    } else {
      injected = styleTag + injected;
    }

    // Inject demo welcome banner if this is a demo conversion
    if (isDemoConversion) {
      var bodyIdx = injected.indexOf("<body");
      if (bodyIdx !== -1) {
        var bodyClose = injected.indexOf(">", bodyIdx);
        if (bodyClose !== -1) {
          injected = injected.slice(0, bodyClose + 1) + DEMO_BANNER_HTML + injected.slice(bodyClose + 1);
        }
      }
      isDemoConversion = false;
    }

    outputFrame.srcdoc = injected;
  }

  // After iframe loads, rewrite links to open in new tab
  outputFrame.addEventListener("load", function () {
    try {
      var doc = outputFrame.contentDocument;
      if (!doc) return;

      // Resolve relative hrefs against the source origin (URL conversions only)
      var origin = "";
      if (currentSourceUrl) {
        try { origin = new URL(currentSourceUrl).origin; } catch (e) { /* malformed */ }
      }

      doc.querySelectorAll("a[href]").forEach(function (a) {
        var href = a.getAttribute("href");
        if (origin && href && !/^https?:\/\/|^#|^mailto:/i.test(href)) {
          a.setAttribute("href", origin + href);
        }
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
      });

      // Demo banner dismiss (inline scripts blocked by sandbox)
      var dismissBtn = doc.getElementById("decant-demo-dismiss");
      if (dismissBtn) {
        dismissBtn.addEventListener("click", function () {
          var banner = dismissBtn.closest(".decant-demo-banner");
          if (banner) banner.remove();
        });
      }
    } catch (e) { /* cross-origin or sandbox restriction */ }
  });

  // --- Sync controls to settings state ---

  function syncControlsToSettings() {
    if (fontSizeSlider) fontSizeSlider.value = settings.fontSize;

    document.querySelectorAll(".font-btn").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-font") === settings.font);
    });

    document.querySelectorAll(".theme-swatch").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-theme") === settings.theme);
    });

    document.querySelectorAll(".spacing-btn").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-spacing") === settings.spacing);
    });

    document.querySelectorAll(".width-btn").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-width") === settings.width);
    });
  }

  function onSettingChange() {
    saveSettings();
    syncControlsToSettings();
    applyOuterTheme();
    applyToIframe();
  }

  // --- Dropdown open/close ---

  function resetHelpViews() {
    document.querySelectorAll(".help-popup-body .help-view").forEach(function (el) {
      el.style.display = "none";
    });
    var chooser = document.getElementById("help-chooser");
    if (chooser) chooser.style.display = "";
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".dropdown.open").forEach(function (el) {
      el.classList.remove("open");
    });
    toolbarContainer.classList.remove("dropdown-open");
    resetHelpViews();
  }

  function toggleDropdown(dropdownEl) {
    var wasOpen = dropdownEl.classList.contains("open");
    closeAllDropdowns();
    if (!wasOpen) {
      dropdownEl.classList.add("open");
      toolbarContainer.classList.add("dropdown-open");
      if (dropdownEl.classList.contains("help-dropdown")) {
        var rect = dropdownEl.getBoundingClientRect();
        var available = window.innerHeight - rect.top - 16;
        var helpBody = dropdownEl.querySelector(".help-popup-body");
        if (helpBody) {
          helpBody.style.maxHeight = available + "px";
        }
      }
    }
  }

  // Single document-level handler for all dropdown open/close
  document.addEventListener("click", function (e) {
    // If clicking a dropdown toggle, toggle that dropdown
    var toggle = e.target.closest(".dropdown-toggle");
    if (toggle) {
      var dropdown = toggle.closest(".dropdown");
      if (dropdown) toggleDropdown(dropdown);
      return;
    }
    // If clicking inside a popup, do nothing (keep it open)
    if (e.target.closest(".dropdown-popup")) return;
    // Otherwise close all dropdowns
    closeAllDropdowns();
  });

  // Help popout sub-view navigation (event delegation)
  document.addEventListener("click", function (e) {
    var navBtn = e.target.closest(".help-nav-btn");
    if (navBtn) {
      var targetId = navBtn.getAttribute("data-help-target");
      var target = document.getElementById(targetId);
      if (target) {
        document.getElementById("help-chooser").style.display = "none";
        target.style.display = "";
      }
      return;
    }
    var backBtn = e.target.closest(".help-back-btn");
    if (backBtn) {
      resetHelpViews();
      return;
    }
  });

  // Escape closes dropdowns
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAllDropdowns();
  });

  // Close dropdowns when mouse enters the iframe (iframe eats click events)
  outputFrame.addEventListener("mouseenter", function () {
    closeAllDropdowns();
  });

  // --- Conversion ---

  function handleConversion(formData, sourceUrl) {
    showLoading();

    fetch("/convert", { method: "POST", body: formData })
      .then(function (resp) {
        return resp.json().then(function (data) {
          return { resp: resp, data: data };
        });
      })
      .then(function (result) {
        if (result.data.status === "ok") {
          showResult(result.data.html, sourceUrl);
        } else {
          handleErrorResponse(result.resp, result.data);
        }
      })
      .catch(function () {
        showError(
          "Couldn't connect to the server.",
          "Check your internet connection and try again."
        );
      });
  }

  function convertUrl(url) {
    // Clear file input state, reset drop zone text
    fileInput.value = "";
    dropZone.querySelector("p").textContent = dropZoneDefault;
    var formData = new FormData();
    formData.append("url", url);
    handleConversion(formData, url);
  }

  function convertFile(file) {
    // Clear URL input, show filename in drop zone
    urlInput.value = "";
    dropZone.querySelector("p").textContent = file.name;
    var formData = new FormData();
    formData.append("file", file);
    handleConversion(formData, "");
  }

  // --- Event listeners: input ---

  urlForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var url = urlInput.value.trim();
    if (url) {
      convertUrl(url);
    }
  });

  // Clear button visibility
  urlInput.addEventListener("input", function () {
    urlClear.classList.toggle("hidden", !urlInput.value);
  });

  urlClear.addEventListener("click", function () {
    urlInput.value = "";
    urlClear.classList.add("hidden");
    urlInput.focus();
  });

  dropZone.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
      convertFile(fileInput.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach(function (evt) {
    dropZone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(function (evt) {
    dropZone.addEventListener(evt, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("dragover");
    });
  });

  dropZone.addEventListener("drop", function (e) {
    var files = e.dataTransfer.files;
    if (files.length > 0) {
      convertFile(files[0]);
    }
  });

  document.addEventListener("dragover", function (e) { e.preventDefault(); });
  document.addEventListener("drop", function (e) { e.preventDefault(); });

  // --- Event listeners: text controls ---

  // Font choice
  document.querySelectorAll(".font-btn").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.font = el.getAttribute("data-font");
      onSettingChange();
    });
  });

  // Font size
  if (fontSizeSlider) {
    fontSizeSlider.addEventListener("input", function () {
      settings.fontSize = parseInt(fontSizeSlider.value, 10);
      onSettingChange();
    });
  }

  // Width
  document.querySelectorAll(".width-btn").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.width = el.getAttribute("data-width");
      onSettingChange();
    });
  });

  // Spacing
  document.querySelectorAll(".spacing-btn").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.spacing = el.getAttribute("data-spacing");
      onSettingChange();
    });
  });

  // Theme swatches
  document.querySelectorAll(".theme-swatch").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.theme = el.getAttribute("data-theme");
      onSettingChange();
    });
  });

  // Reset
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      settings = JSON.parse(JSON.stringify(DEFAULTS));
      onSettingChange();
    });
  }

  // --- Save actions ---

  document.getElementById("print-btn").addEventListener("click", function () {
    var content = outputFrame.srcdoc || currentHtml;
    if (!content) return;
    var printStyle = "<style>@media print { " +
      "body { background: white !important; color: black !important; } " +
      "a { color: #1856a8 !important; } }</style>";
    if (content.indexOf("</head>") !== -1) {
      content = content.replace("</head>", printStyle + "</head>");
    } else {
      content = printStyle + content;
    }
    var blob = new Blob([content], { type: "text/html" });
    var blobUrl = URL.createObjectURL(blob);
    var printWindow = window.open(blobUrl);
    printWindow.onload = function () {
      printWindow.print();
    };
    setTimeout(function () {
      URL.revokeObjectURL(blobUrl);
    }, 60000);
    closeAllDropdowns();
  });

  document.getElementById("download-html-btn").addEventListener("click", function () {
    if (!currentHtml) return;
    var filename = "decant.html";
    try {
      var parsed = new DOMParser().parseFromString(currentHtml, "text/html");
      var titleEl = parsed.querySelector("title");
      if (titleEl && titleEl.textContent) {
        var slug = titleEl.textContent.toLowerCase().trim()
          .replace(/[^a-z0-9\s-]/g, "")
          .replace(/[\s]+/g, "-")
          .replace(/-{2,}/g, "-")
          .replace(/^-|-$/g, "");
        if (slug) filename = slug + ".html";
      }
    } catch (e) { /* fall back to default */ }
    var blob = new Blob([currentHtml], { type: "text/html" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    closeAllDropdowns();
  });

  // --- Share + View Original ---

  function showToast(message) {
    var el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(function () {
      el.classList.add("toast-fade");
    }, 2000);
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 2500);
  }

  document.getElementById("share-btn").addEventListener("click", function () {
    if (!currentSourceUrl) return;
    var shareUrl = "https://decant.cc?url=" + encodeURIComponent(currentSourceUrl);
    navigator.clipboard.writeText(shareUrl).then(function () {
      showToast("Link copied");
    });
  });

  document.getElementById("view-original-btn").addEventListener("click", function () {
    if (!currentSourceUrl) return;
    window.open(currentSourceUrl, "_blank", "noopener,noreferrer");
  });

  // --- Feedback ---

  function sendFeedback(rating, text) {
    var source = currentSourceUrl || "file_upload";
    fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: source,
        rating: rating,
        text: text || "",
        timestamp: new Date().toISOString()
      })
    }).catch(function () { /* silent */ });
  }

  function handleThumbClick(rating, btn, other) {
    btn.classList.add("active");
    other.classList.remove("active");
    feedbackExpand.classList.remove("hidden");
    sendFeedback(rating, "");
  }

  feedbackUp.addEventListener("click", function () {
    handleThumbClick("up", feedbackUp, feedbackDown);
  });

  feedbackDown.addEventListener("click", function () {
    handleThumbClick("down", feedbackDown, feedbackUp);
  });

  feedbackSubmit.addEventListener("click", function () {
    var rating = feedbackUp.classList.contains("active") ? "up" : "down";
    var text = feedbackText.value.trim();
    if (text) {
      sendFeedback(rating, text);
      feedbackText.value = "";
      feedbackExpand.classList.add("hidden");
    }
  });

  // --- Try demo ---

  if (tryDemoBtn) {
    tryDemoBtn.addEventListener("click", function () {
      closeAllDropdowns();
      isDemoConversion = true;
      var demoUrl = "https://decant.cc/demo";
      urlInput.value = demoUrl;
      urlClear.classList.remove("hidden");
      convertUrl(demoUrl);
    });
  }

  // --- Init ---

  applyOuterTheme();
  syncControlsToSettings();

  // Enable transitions after initial paint (prevents flash on load)
  requestAnimationFrame(function () {
    document.body.classList.add("loaded");
  });

  if (window.__prefilled_url) {
    urlInput.value = window.__prefilled_url;
    convertUrl(window.__prefilled_url);
  }
})();
