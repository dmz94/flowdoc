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
  var viewOriginalLink = document.getElementById("view-original");
  var errorContainer = document.getElementById("error");
  var errorMessage = document.getElementById("error-message");
  var errorHint = document.getElementById("error-hint");
  var convertingStatus = document.getElementById("converting");
  var settingsBtn = document.getElementById("settings-btn");
  var settingsPanel = document.getElementById("settings-panel");
  var settingsOverlay = document.getElementById("settings-overlay");
  var panelClose = document.getElementById("panel-close");
  var fontSizeSlider = document.getElementById("font-size-slider");
  var spacingLabel = document.getElementById("spacing-label");
  var resetBtn = document.getElementById("reset-btn");
  var widthLabel = document.getElementById("width-label");
  var pageWrapper = document.querySelector(".page-wrapper");

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
    light: {
      bg: "#fafaf7", text: "#333", link: "#1a0dab", visited: "#660099",
      inputBg: "#fff", inputBorder: "#ccc", mutedText: "#999",
      badgeBg: "transparent", buttonBorder: "#ddd",
      convertBg: "#333", convertText: "#fff",
      errorBg: "#fff8f8", errorBorder: "#cc3333"
    },
    cream: {
      bg: "#f5f0e8", text: "#333", link: "#1a0dab", visited: "#660099",
      inputBg: "#fff", inputBorder: "#ccc", mutedText: "#999",
      badgeBg: "transparent", buttonBorder: "#ddd",
      convertBg: "#333", convertText: "#fff",
      errorBg: "#fff8f8", errorBorder: "#cc3333"
    },
    dark: {
      bg: "#1e1e1e", text: "#e0e0e0", link: "#6db3f2", visited: "#c4a4ff",
      inputBg: "#2a2a2a", inputBorder: "#555", mutedText: "#888",
      badgeBg: "#444", buttonBorder: "#666",
      convertBg: "#e0e0e0", convertText: "#1e1e1e",
      errorBg: "#2a1a1a", errorBorder: "#cc3333"
    },
    contrast: {
      bg: "#1a1a1a", text: "#ffd700", link: "#ffd700", visited: "#ff80ab",
      inputBg: "#2a2a2a", inputBorder: "#ffd700", mutedText: "#ccc",
      badgeBg: "rgba(255, 215, 0, 0.15)", buttonBorder: "#ffd700",
      convertBg: "#ffd700", convertText: "#1a1a1a",
      errorBg: "#2a1a1a", errorBorder: "#ffd700"
    }
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
    settingsBtn.classList.remove("hidden");

    currentHtml = html;
    currentSourceUrl = sourceUrl;

    applyToIframe();

    if (sourceUrl) {
      viewOriginalLink.href = sourceUrl;
      viewOriginalLink.classList.remove("hidden");
    } else {
      viewOriginalLink.classList.add("hidden");
    }
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

    return css.join("\n");
  }

  function applyOuterTheme() {
    var theme = THEMES[settings.theme] || THEMES.light;

    // Background on body and wrapper elements
    document.body.style.backgroundColor = theme.bg;
    var bgEls = document.querySelectorAll(
      ".page-wrapper, .container, .output-zone, .result-bar, .site-header"
    );
    bgEls.forEach(function (el) {
      el.style.backgroundColor = theme.bg;
    });

    // Site title
    var siteTitle = document.querySelector(".site-title");
    if (siteTitle) siteTitle.style.color = theme.text;

    // URL input
    var urlField = document.querySelector(".url-form input[type='text']");
    if (urlField) {
      urlField.style.backgroundColor = theme.inputBg;
      urlField.style.color = theme.text;
      urlField.style.borderColor = theme.inputBorder;
    }

    // Convert button
    var convertBtn = document.querySelector(".url-form button");
    if (convertBtn) {
      convertBtn.style.backgroundColor = theme.convertBg;
      convertBtn.style.color = theme.convertText;
    }

    // Drop zone
    var dz = document.querySelector(".drop-zone");
    if (dz) {
      dz.style.borderColor = theme.inputBorder;
      dz.style.color = theme.mutedText;
    }

    // Or divider
    var orDiv = document.querySelector(".or-divider");
    if (orDiv) orDiv.style.color = theme.mutedText;

    // Settings button (in header, NOT in panel)
    var sb = document.querySelector(".settings-btn");
    if (sb) {
      sb.style.borderColor = theme.buttonBorder;
      sb.style.color = theme.text;
    }

    // Settings badge
    var badge = document.querySelector(".settings-badge");
    if (badge) {
      badge.style.backgroundColor = theme.badgeBg;
      badge.style.color = theme.text;
    }

    // View Original link
    var voLink = document.querySelector(".view-original-link");
    if (voLink) {
      voLink.style.borderColor = theme.buttonBorder;
      voLink.style.color = theme.text;
    }

    // View Original badge
    var voBadge = document.querySelector(".view-original-badge");
    if (voBadge) voBadge.style.backgroundColor = theme.badgeBg;

    // Error container
    var errCont = document.querySelector(".error-container");
    if (errCont) {
      errCont.style.backgroundColor = theme.errorBg;
      errCont.style.color = theme.text;
      errCont.style.borderLeftColor = theme.errorBorder;
    }

    var errHint = document.querySelector(".error-hint");
    if (errHint) errHint.style.color = theme.mutedText;

    // Align result-bar width with content width
    var resultBar = document.querySelector(".result-bar");
    if (resultBar) {
      resultBar.style.maxWidth = WIDTH_VALUES[settings.width] || WIDTH_VALUES.medium;
    }
  }

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

    outputFrame.srcdoc = injected;
  }

  // --- Settings panel ---

  function openPanel() {
    settingsPanel.classList.add("open");
    settingsOverlay.classList.remove("hidden");
    outputSection.style.marginRight = "320px";
  }

  function closePanel() {
    settingsPanel.classList.remove("open");
    settingsOverlay.classList.add("hidden");
    outputSection.style.marginRight = "0";
  }

  function togglePanel() {
    if (settingsPanel.classList.contains("open")) {
      closePanel();
    } else {
      openPanel();
    }
  }

  // --- Sync controls to settings state ---

  function syncControlsToSettings() {
    // Font size slider
    fontSizeSlider.value = settings.fontSize;

    // Theme swatches
    document.querySelectorAll(".theme-swatch").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-theme") === settings.theme);
    });

    // Font radios
    document.querySelectorAll('input[name="font"]').forEach(function (el) {
      el.checked = el.value === settings.font;
    });

    // Spacing buttons
    document.querySelectorAll(".spacing-btn").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-spacing") === settings.spacing);
    });
    spacingLabel.textContent = SPACING_LABELS[settings.spacing] || "Standard";

    // Width buttons
    document.querySelectorAll(".width-btn").forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-width") === settings.width);
    });
    widthLabel.textContent = WIDTH_LABELS[settings.width] || "Medium";
  }

  function onSettingChange() {
    saveSettings();
    applyToIframe();
  }

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
    var formData = new FormData();
    formData.append("url", url);
    handleConversion(formData, url);
  }

  function convertFile(file) {
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

  // --- Event listeners: settings panel ---

  settingsBtn.addEventListener("click", togglePanel);
  panelClose.addEventListener("click", closePanel);
  settingsOverlay.addEventListener("click", closePanel);

  // A. Font size
  fontSizeSlider.addEventListener("input", function () {
    settings.fontSize = parseInt(fontSizeSlider.value, 10);
    onSettingChange();
  });

  // B. Theme
  document.querySelectorAll(".theme-swatch").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.theme = el.getAttribute("data-theme");
      syncControlsToSettings();
      onSettingChange();
    });
  });

  // C. Font
  document.querySelectorAll('input[name="font"]').forEach(function (el) {
    el.addEventListener("change", function () {
      settings.font = el.value;
      onSettingChange();
    });
  });

  // D. Spacing
  document.querySelectorAll(".spacing-btn").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.spacing = el.getAttribute("data-spacing");
      syncControlsToSettings();
      onSettingChange();
    });
  });

  // E. Width
  document.querySelectorAll(".width-btn").forEach(function (el) {
    el.addEventListener("click", function () {
      settings.width = el.getAttribute("data-width");
      syncControlsToSettings();
      onSettingChange();
    });
  });

  // F. Reset
  resetBtn.addEventListener("click", function () {
    settings = JSON.parse(JSON.stringify(DEFAULTS));
    syncControlsToSettings();
    onSettingChange();
  });

  // --- Init ---

  syncControlsToSettings();

  if (window.__prefilled_url) {
    urlInput.value = window.__prefilled_url;
    convertUrl(window.__prefilled_url);
  }
})();
