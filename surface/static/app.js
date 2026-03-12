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
    light:    { bg: "#fafaf7", text: "#333",    link: "#1856a8", visited: "#694598" },
    cream:    { bg: "#f5f0e8", text: "#333",    link: "#3a6ea5", visited: "#8b5e83" },
    dark:     { bg: "#1e1e1e", text: "#e0e0e0", link: "#6db3f2", visited: "#c4a4ff" },
    contrast: { bg: "#1a1a1a", text: "#ffd700", link: "#00e5ff", visited: "#ff80ab" }
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

  function closeAllDropdowns() {
    document.querySelectorAll(".dropdown.open").forEach(function (el) {
      el.classList.remove("open");
    });
    toolbarContainer.classList.remove("dropdown-open");
  }

  function toggleDropdown(dropdownEl) {
    var wasOpen = dropdownEl.classList.contains("open");
    closeAllDropdowns();
    if (!wasOpen) {
      dropdownEl.classList.add("open");
      toolbarContainer.classList.add("dropdown-open");
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
