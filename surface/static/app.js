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
  var inlineError = document.getElementById("inline-error");
  var inlineErrorMessage = document.getElementById("inline-error-message");
  var inlineErrorHint = document.getElementById("inline-error-hint");
  var convertingStatus = document.getElementById("converting");
  var toolbarContainer = document.getElementById("toolbar-container");
  var fontSizeSlider = document.getElementById("font-size-slider");
  var resetBtn = document.getElementById("reset-btn");
  var feedbackWidget = document.getElementById("feedback-widget");
  var feedbackOptions = document.getElementById("feedback-widget");
  var feedbackRadios = document.querySelectorAll('input[name="feedback-rating"]');
  var feedbackThanks = document.getElementById("feedback-thanks");
  var feedbackUpdateBtn = document.getElementById("feedback-update");
  var feedbackExpand = document.getElementById("feedback-expand");
  var feedbackText = document.getElementById("feedback-text");
  var feedbackSubmit = document.getElementById("feedback-submit");
  var urlClear = document.getElementById("url-clear");
  var tryDemoBtn = document.getElementById("try-demo-btn");
  var articleOverlay = document.getElementById("article-overlay");
  var articleOverlayStatus = document.getElementById("article-overlay-status");
  var srAnnouncer = document.getElementById("sr-announcer");
  var errorFeedback = document.getElementById("error-feedback");
  var errorFeedbackToggle = document.getElementById("error-feedback-toggle");
  var errorFeedbackForm = document.getElementById("error-feedback-form");
  var errorFeedbackText = document.getElementById("error-feedback-text");
  var errorFeedbackSubmit = document.getElementById("error-feedback-submit");
  var errorFeedbackThanks = document.getElementById("error-feedback-thanks");

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
    light:    { bg: "#fafaf7", text: "#333",    link: "#1856a8", visited: "#694598", notice: { bg: "#f0f0e8", border: "#b0a870", text: "#555555" } },
    cream:    { bg: "#f5f0e8", text: "#333",    link: "#3a6ea5", visited: "#8b5e83", notice: { bg: "#e8dfca", border: "#a08860", text: "#5b4636" } },
    dark:     { bg: "#1e1e1e", text: "#e0e0e0", link: "#6db3f2", visited: "#c4a4ff", notice: { bg: "rgb(55, 54, 66)", border: "rgb(140, 140, 160)", text: "rgb(200, 200, 210)" } },
    contrast: { bg: "#1a1a1a", text: "#ffd700", link: "#00e5ff", visited: "#ff80ab", notice: { bg: "#000000", border: "#ffee32", text: "#ffffff" } }
  };

  var WIDTH_VALUES = { narrow: "38em", medium: "48em", wide: "60em" };
  var WIDTH_LABELS = { narrow: "Narrow", medium: "Medium", wide: "Wide" };

  var SPACING_VALUES = {
    standard: null,
    loose: { letterSpacing: "0.08em", wordSpacing: "0.3em", lineHeight: "1.8" },
    veryloose: { letterSpacing: "0.14em", wordSpacing: "0.45em", lineHeight: "2.1" }
  };

  var SPACING_LABELS = { standard: "Standard", loose: "Loose", veryloose: "Very Loose" };

  var BLOCKED_EXTENSIONS = [
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".mp3", ".mp4", ".zip", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx"
  ];

  var settings = loadSettings();
  var currentSourceUrl = "";
  var currentHtml = "";
  var isDemoConversion = false;
  var navigationCounter = 0;
  var activeNavigationId = 0;
  var articleCache = new Map();
  var cacheIdCounter = 0;
  var pendingScrollRestore = null;
  var pendingFocusHeading = false;
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

  // --- Feedback state ---

  var feedbackInteractionId = "";
  var feedbackSubmitted = false;
  var errorFeedbackInteractionId = "";
  var errorAttemptedUrl = "";
  var errorErrorType = "";
  var errorFeedbackSubmitted = false;

  function generateInteractionId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function getViewport() {
    var w = window.innerWidth;
    if (w <= 430) return "phone";
    if (w <= 768) return "tablet";
    return "desktop";
  }

  function getSourceDomain(url) {
    try { return new URL(url).hostname; } catch (e) { return ""; }
  }

  function getSelectedRating() {
    var checked = document.querySelector('input[name="feedback-rating"]:checked');
    return checked ? checked.value : "";
  }

  // --- Demo overlay ---

  function dismissDemoOverlay() {
    var existing = document.getElementById("demo-overlay");
    if (existing) existing.remove();
    var voBtn = document.getElementById("view-original-btn");
    if (voBtn) voBtn.classList.remove("toolbar-highlight");
  }

  function showDemoOverlay() {
    dismissDemoOverlay();

    var overlay = document.createElement("div");
    overlay.id = "demo-overlay";
    overlay.className = "demo-overlay-backdrop";

    var card = document.createElement("div");
    card.className = "demo-overlay-card";

    card.innerHTML =
      '<div class="demo-overlay-badge">Demo</div>' +
      '<p>The clean article behind this card is our test page, ' +
      'cleaned up by Decant.</p>' +
      '<p>The original is full of ads, pop-ups, and clutter.</p>' +
      '<p class="demo-vo-hint">' +
      '<svg class="demo-vo-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" ' +
      'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M6 2H2v12h12v-4"/>' +
      '<path d="M9 2h5v5"/>' +
      '<path d="M7 9L14 2"/>' +
      '</svg> ' +
      '<strong>View Original</strong> in the toolbar lets you ' +
      'compare anytime.</p>' +
      '<p>Click below now to see it for yourself.</p>' +
      '<div class="demo-overlay-actions">' +
      '<button type="button" class="demo-overlay-btn demo-overlay-primary">' +
      'See the original &rarr;</button>' +
      '<button type="button" class="demo-overlay-btn demo-overlay-secondary">' +
      'Got it</button>' +
      '</div>';

    overlay.appendChild(card);
    outputSection.appendChild(overlay);

    // "See the original" opens the original page
    card.querySelector(".demo-overlay-primary").addEventListener("click", function () {
      if (currentSourceUrl) {
        window.open(currentSourceUrl, "_blank", "noopener,noreferrer");
      }
    });

    // "Got it" dismisses
    card.querySelector(".demo-overlay-secondary").addEventListener("click", dismissDemoOverlay);

    // Clicking backdrop dismisses
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) dismissDemoOverlay();
    });

    // Make the inline icon clickable too (same as View Original)
    var voIcon = card.querySelector(".demo-vo-icon");
    if (voIcon) {
      voIcon.style.cursor = "pointer";
      voIcon.addEventListener("click", function () {
        if (currentSourceUrl) {
          window.open(currentSourceUrl, "_blank", "noopener,noreferrer");
        }
      });
    }

    // Also make the "View Original" text clickable
    var voStrong = card.querySelector(".demo-vo-hint strong");
    if (voStrong) {
      voStrong.style.cursor = "pointer";
      voStrong.addEventListener("click", function () {
        if (currentSourceUrl) {
          window.open(currentSourceUrl, "_blank", "noopener,noreferrer");
        }
      });
    }

    var voBtn = document.getElementById("view-original-btn");
    if (voBtn) voBtn.classList.add("toolbar-highlight");
  }

  // --- UI state helpers ---

  function populateHint(hintEl, hint, hintUrl) {
    hintEl.textContent = "";
    if (hint && hintUrl) {
      var link = document.createElement("a");
      link.href = hintUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = hint;
      hintEl.appendChild(link);
    } else {
      hintEl.textContent = hint || "";
    }
  }

  function showError(message, hint, hintUrl, options) {
    var mode = (options && options.mode) || "destructive";

    if (mode === "preserving") {
      inlineErrorMessage.textContent = message;
      populateHint(inlineErrorHint, hint, hintUrl);
      inlineError.classList.remove("hidden");
    } else {
      errorMessage.textContent = message;
      populateHint(errorHint, hint, hintUrl);
      errorContainer.classList.remove("hidden");
      outputSection.classList.add("hidden");
      convertingStatus.classList.add("hidden");
      // Hide toolbar buttons from previous conversion
      document.querySelectorAll(".action-only").forEach(function (el) {
        el.classList.add("hidden");
      });
      currentSourceUrl = "";
      currentHtml = "";
      errorFeedbackForm.classList.add("hidden");
      errorFeedbackThanks.classList.add("hidden");
      errorFeedbackToggle.classList.remove("hidden");
      errorFeedbackText.value = "";
      errorFeedback.classList.remove("hidden");
    }
  }

  function hideError() {
    errorContainer.classList.add("hidden");
    inlineError.classList.add("hidden");
    errorFeedback.classList.add("hidden");
  }

  function showArticleOverlay(statusText) {
    articleOverlayStatus.textContent = statusText || "Loading...";
    articleOverlay.classList.remove("hidden");
  }

  function hideArticleOverlay() {
    articleOverlay.classList.add("hidden");
  }

  function announce(text) {
    srAnnouncer.textContent = "";
    requestAnimationFrame(function () {
      srAnnouncer.textContent = text;
    });
  }

  function beginArticleNavigation(statusText) {
    pendingScrollRestore = null;
    pendingFocusHeading = false;
    navigationCounter++;
    activeNavigationId = navigationCounter;
    hideError();
    showArticleOverlay(statusText);
    return activeNavigationId;
  }

  function completeArticleNavigation(requestId) {
    if (requestId !== activeNavigationId) return false;
    activeNavigationId = 0;
    hideArticleOverlay();
    return true;
  }

  function failArticleNavigation(requestId, mode, message, hint, hintUrl) {
    if (requestId !== activeNavigationId) return false;
    activeNavigationId = 0;
    hideArticleOverlay();
    showError(message, hint, hintUrl, { mode: mode || "preserving" });
    return true;
  }

  function isNavigationInProgress() {
    return activeNavigationId !== 0;
  }

  function showLoading(options) {
    var mode = (options && options.mode) || "destructive";
    hideError();

    if (mode === "preserving") {
      // Intentionally minimal: clear errors without disturbing current article
    } else {
      outputSection.classList.add("hidden");
      convertingStatus.classList.remove("hidden");
    }
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
    feedbackRadios.forEach(function (r) { r.checked = false; });
    feedbackExpand.classList.add("hidden");
    feedbackThanks.classList.add("hidden");
    feedbackText.value = "";
    feedbackInteractionId = generateInteractionId();
    feedbackSubmitted = false;
    feedbackWidget.classList.remove("feedback-submitted");

    // Show demo welcome overlay if triggered from "Try the demo"
    if (isDemoConversion) {
      showDemoOverlay();
      isDemoConversion = false;
    } else {
      dismissDemoOverlay();
    }

    applyToIframe();
  }

  function handleErrorResponse(resp, data, options) {
    var message = (data && data.message) || "Conversion failed.";
    var hint = "";
    var hintUrl = "";
    var status = resp.status;

    if (data && data.hint) {
      hint = data.hint;
      hintUrl = data.hint_url || "";
    } else if (status === 429) {
      hint = "You can try again shortly.";
    } else if (status === 500) {
      hint = "If this keeps happening, the page may not be compatible.";
    }

    errorErrorType = (data && data.error_type) || "";
    errorAttemptedUrl = (options && options.attemptedUrl !== undefined) ? options.attemptedUrl : (urlInput.value || "");
    errorFeedbackInteractionId = generateInteractionId();
    errorFeedbackSubmitted = false;

    showError(message, hint, hintUrl, options);
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

  // --- Link interception ---

  function extractArticleTitle(html, sourceUrl) {
    try {
      var match = html.match(/<title[^>]*>([^<]*)<\/title>/i);
      if (match && match[1].trim()) return match[1].trim();
    } catch (e) {}
    if (sourceUrl) {
      try { return new URL(sourceUrl).hostname; } catch (e) {}
    }
    return "Article";
  }

  function captureScrollPosition() {
    try {
      var se = outputFrame.contentDocument.scrollingElement
            || outputFrame.contentDocument.documentElement;
      return se.scrollTop || 0;
    } catch (e) {
      return 0;
    }
  }

  function addToCache(sourceUrl, articleHtml, title) {
    cacheIdCounter++;
    var id = cacheIdCounter;
    articleCache.set(id, {
      sourceUrl: sourceUrl,
      articleHtml: articleHtml,
      title: title
    });
    if (articleCache.size > 10) {
      var oldest = articleCache.keys().next().value;
      articleCache.delete(oldest);
    }
    return id;
  }

  function isQualifyingLink(href, baseUrl) {
    var resolved;
    try {
      resolved = new URL(href, baseUrl);
    } catch (e) {
      return null;
    }
    if (resolved.protocol !== "http:" && resolved.protocol !== "https:") {
      return null;
    }
    var pathname = resolved.pathname.toLowerCase();
    for (var i = 0; i < BLOCKED_EXTENSIONS.length; i++) {
      if (pathname.endsWith(BLOCKED_EXTENSIONS[i])) {
        return null;
      }
    }
    return resolved;
  }

  function isSameArticle(resolvedUrl) {
    if (!currentSourceUrl) return false;
    try {
      var current = new URL(currentSourceUrl);
      var a = resolvedUrl.origin + resolvedUrl.pathname + resolvedUrl.search;
      var b = current.origin + current.pathname + current.search;
      return a === b;
    } catch (e) {
      return false;
    }
  }

  function handleInterceptedNavigation(url) {
    // Capture current scroll position before navigating away
    var scrollTop = captureScrollPosition();

    // Save scroll position into current history entry
    var currentState = history.state;
    if (currentState && currentState.cacheId !== undefined) {
      history.replaceState({
        sourceUrl: currentState.sourceUrl,
        title: currentState.title,
        scrollTop: scrollTop,
        cacheId: currentState.cacheId
      }, "", location.href);
    }

    var requestId = beginArticleNavigation("Converting...");

    var formData = new FormData();
    formData.append("url", url);

    fetch("/convert", { method: "POST", body: formData })
      .then(function (resp) {
        return resp.json().then(function (data) {
          return { resp: resp, data: data };
        });
      })
      .then(function (result) {
        if (result.data.status === "ok") {
          if (!completeArticleNavigation(requestId)) return;
          pendingFocusHeading = true;
          showResult(result.data.html, url);
          urlInput.value = url;
          urlClear.classList.remove("hidden");
          // Add to cache and push history entry
          var title = extractArticleTitle(result.data.html, url);
          var cacheId = addToCache(url, result.data.html, title);
          history.pushState(
            { sourceUrl: url, title: title, scrollTop: 0, cacheId: cacheId },
            "",
            "/?url=" + encodeURIComponent(url)
          );
          announce("Loaded: " + title);
        } else {
          var message = (result.data && result.data.message) || "Conversion failed.";
          var hint = "";
          var hintUrl = "";
          if (result.data && result.data.hint) {
            hint = result.data.hint;
            hintUrl = result.data.hint_url || "";
          } else if (result.resp.status === 429) {
            hint = "You can try again shortly.";
          } else if (result.resp.status === 500) {
            hint = "If this keeps happening, the page may not be compatible.";
          }
          failArticleNavigation(requestId, "preserving", message, hint, hintUrl);
        }
      })
      .catch(function () {
        failArticleNavigation(
          requestId, "preserving",
          "Couldn't connect to the server.",
          "Check your internet connection and try again."
        );
      });
  }

  function handleCacheMissReconversion(state) {
    var requestId = beginArticleNavigation("Restoring...");

    var formData = new FormData();
    formData.append("url", state.sourceUrl);

    fetch("/convert", { method: "POST", body: formData })
      .then(function (resp) {
        return resp.json().then(function (data) {
          return { resp: resp, data: data };
        });
      })
      .then(function (result) {
        if (result.data.status === "ok") {
          if (!completeArticleNavigation(requestId)) return;
          pendingScrollRestore = state.scrollTop || 0;
          showResult(result.data.html, state.sourceUrl);
          urlInput.value = state.sourceUrl;
          urlClear.classList.toggle("hidden", !state.sourceUrl);
          // Re-add to cache and update history entry
          var title = extractArticleTitle(result.data.html, state.sourceUrl);
          var cacheId = addToCache(state.sourceUrl, result.data.html, title);
          history.replaceState({
            sourceUrl: state.sourceUrl,
            title: title,
            scrollTop: state.scrollTop || 0,
            cacheId: cacheId
          }, "", location.href);
        } else {
          var message = (result.data && result.data.message) || "Conversion failed.";
          var hint = "";
          var hintUrl = "";
          if (result.data && result.data.hint) {
            hint = result.data.hint;
            hintUrl = result.data.hint_url || "";
          } else if (result.resp.status === 429) {
            hint = "You can try again shortly.";
          } else if (result.resp.status === 500) {
            hint = "If this keeps happening, the page may not be compatible.";
          }
          failArticleNavigation(requestId, "preserving", message, hint, hintUrl);
        }
      })
      .catch(function () {
        failArticleNavigation(
          requestId, "preserving",
          "This article is no longer cached.",
          "Open the original page",
          state.sourceUrl
        );
      });
  }

  window.addEventListener("popstate", function (e) {
    var state = e.state;

    // Cancel any in-progress navigation
    if (isNavigationInProgress()) {
      activeNavigationId = 0;
      hideArticleOverlay();
    }
    pendingScrollRestore = null;

    // No Decant state -- restore to initial page state
    if (!state || state.cacheId === undefined) {
      outputSection.classList.add("hidden");
      hideError();
      convertingStatus.classList.add("hidden");
      document.querySelectorAll(".action-only").forEach(function (el) {
        el.classList.add("hidden");
      });
      currentSourceUrl = "";
      currentHtml = "";
      urlInput.value = "";
      urlClear.classList.add("hidden");
      return;
    }

    var cached = articleCache.get(state.cacheId);

    if (cached) {
      // Cache hit: restore instantly
      pendingScrollRestore = state.scrollTop || 0;
      showResult(cached.articleHtml, cached.sourceUrl);
      urlInput.value = cached.sourceUrl;
      urlClear.classList.toggle("hidden", !cached.sourceUrl);
    } else {
      // Cache miss: re-convert
      handleCacheMissReconversion(state);
    }
  });

  // Link setup runs on every iframe load. Because applyToIframe()
  // sets srcdoc (which replaces the contentDocument), old listeners
  // are destroyed automatically. This handler re-attaches them.
  outputFrame.addEventListener("load", function () {
    try {
      var doc = outputFrame.contentDocument;
      if (!doc) return;

      var baseUrl = currentSourceUrl || "";

      doc.querySelectorAll("a[href]").forEach(function (a) {
        var rawHref = a.getAttribute("href");

        // Category 1: Fragment-only links scroll within iframe
        if (rawHref && rawHref.charAt(0) === "#") {
          return;
        }

        var href = rawHref;

        // Resolve relative hrefs to absolute
        if (baseUrl && href) {
          try {
            var abs = new URL(href, baseUrl).href;
            a.setAttribute("href", abs);
            href = abs;
          } catch (e) { /* leave malformed href as-is */ }
        }

        // Qualify the link
        var resolved = baseUrl ? isQualifyingLink(href, baseUrl) : null;

        if (!resolved) {
          // Category 4: Non-qualifying -- open in new tab
          a.setAttribute("target", "_blank");
          a.setAttribute("rel", "noopener noreferrer");
        } else if (isSameArticle(resolved)) {
          // Category 2: Same article -- no-op with optional
          // fragment scroll. Without this handler the browser
          // would navigate the iframe to the original URL,
          // destroying the cleaned content.
          a.addEventListener("click", function (e) {
            if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
            e.preventDefault();
            var fragment = resolved.hash ? resolved.hash.slice(1) : "";
            if (fragment && doc) {
              var target = doc.getElementById(fragment);
              if (target) {
                target.scrollIntoView({ behavior: "smooth" });
              }
            }
          });
        } else {
          // Category 3: Qualifying different article -- intercept
          a.addEventListener("click", function (e) {
            if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
            if (isNavigationInProgress()) {
              e.preventDefault();
              return;
            }
            e.preventDefault();
            handleInterceptedNavigation(resolved.href);
          });
        }
      });

      // Restore scroll position if pending (from popstate)
      if (pendingScrollRestore !== null) {
        var scrollTarget = pendingScrollRestore;
        pendingScrollRestore = null;
        var se = doc.scrollingElement || doc.documentElement;
        if (se) {
          se.scrollTop = scrollTarget;
        }
      }

      // Focus primary heading if pending (from new navigation)
      if (pendingFocusHeading) {
        pendingFocusHeading = false;
        var heading = doc.querySelector("h1, h2");
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          heading.focus({ preventScroll: true });
        }
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
        var helpBody = dropdownEl.querySelector(".help-popup-body");
        if (helpBody) {
          if (window.innerWidth <= 430) {
            helpBody.style.maxHeight = "";
          } else {
            var rect = dropdownEl.getBoundingClientRect();
            var available = window.innerHeight - rect.top - 16;
            helpBody.style.maxHeight = available + "px";
          }
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

  // --- Bottom sheet swipe-to-dismiss (phone only) ---

  var phoneMQ = window.matchMedia("(max-width: 430px)");

  document.querySelectorAll(".dropdown-popup").forEach(function (popup) {
    var startY = 0;
    var startTime = 0;
    var dragInitiated = false;
    var dragRejected = false;
    var currentDeltaY = 0;

    function hasScrollableContent(el) {
      var children = el.querySelectorAll(".help-popup-body, .popup-body, .theme-popup-body, .save-popup-body");
      for (var i = 0; i < children.length; i++) {
        if (children[i].scrollHeight > children[i].clientHeight) return children[i];
      }
      return null;
    }

    function resetPopup() {
      popup.style.transform = "";
      popup.style.opacity = "";
      popup.classList.remove("dragging", "dismissing");
    }

    popup.addEventListener("touchstart", function (e) {
      if (!phoneMQ.matches) return;
      var touch = e.touches[0];
      startY = touch.clientY;
      startTime = Date.now();
      dragInitiated = false;
      dragRejected = false;
      currentDeltaY = 0;
    }, { passive: true });

    popup.addEventListener("touchmove", function (e) {
      if (!phoneMQ.matches || dragRejected) return;
      var touch = e.touches[0];
      var deltaY = touch.clientY - startY;

      if (!dragInitiated) {
        if (deltaY <= 0) {
          dragRejected = true;
          return;
        }
        var popupRect = popup.getBoundingClientRect();
        var touchInHandle = (startY - popupRect.top) < 24;
        var scrollable = hasScrollableContent(popup);
        if (!touchInHandle && scrollable && scrollable.scrollTop > 0) {
          dragRejected = true;
          return;
        }
        dragInitiated = true;
        popup.classList.add("dragging");
      }

      e.preventDefault();
      currentDeltaY = deltaY * 0.6;
      popup.style.transform = "translateY(" + currentDeltaY + "px)";
    }, { passive: false });

    popup.addEventListener("touchend", function () {
      if (!phoneMQ.matches || !dragInitiated) return;
      popup.classList.remove("dragging");

      var elapsed = Date.now() - startTime;
      var velocity = currentDeltaY / elapsed;
      var popupHeight = popup.offsetHeight;

      if (velocity > 0.5 || currentDeltaY > popupHeight * 0.3) {
        popup.classList.add("dismissing");
        popup.style.transform = "translateY(" + (popupHeight + 40) + "px)";
        popup.style.opacity = "0";
        popup.addEventListener("transitionend", function onEnd() {
          popup.removeEventListener("transitionend", onEnd);
          closeAllDropdowns();
          resetPopup();
        });
      } else {
        popup.style.transform = "translateY(0)";
        popup.addEventListener("transitionend", function onEnd() {
          popup.removeEventListener("transitionend", onEnd);
          resetPopup();
        });
      }
    }, { passive: true });
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
          if (sourceUrl) {
            var title = extractArticleTitle(result.data.html, sourceUrl);
            var cacheId = addToCache(sourceUrl, result.data.html, title);
            history.replaceState(
              { sourceUrl: sourceUrl, title: title, scrollTop: 0, cacheId: cacheId },
              "",
              "/?url=" + encodeURIComponent(sourceUrl)
            );
          }
        } else {
          handleErrorResponse(result.resp, result.data, { attemptedUrl: sourceUrl });
        }
      })
      .catch(function () {
        errorErrorType = "network_error";
        errorAttemptedUrl = sourceUrl || "";
        errorFeedbackInteractionId = generateInteractionId();
        errorFeedbackSubmitted = false;
        showError(
          "Couldn't connect to the server.",
          "Check your internet connection and try again."
        );
      });
  }

  function convertUrl(url) {
    // Auto-prepend https:// if no protocol given
    if (!/^https?:\/\//i.test(url)) {
      url = "https://" + url;
      urlInput.value = url;
    }
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
    var now = new Date().toISOString();
    var payload = {
      interaction_id: feedbackInteractionId,
      source: source,
      source_domain: getSourceDomain(source),
      rating: rating,
      text: text || "",
      viewport: getViewport(),
      theme: settings.theme === "cream" ? "sepia" : settings.theme,
      timestamp: now
    };
    if (!feedbackSubmitted) {
      payload.created_at = now;
    }
    payload.updated_at = now;

    fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(function () { /* silent */ });
  }

  function sendErrorFeedback(text) {
    var source = errorAttemptedUrl || "file_upload";
    var now = new Date().toISOString();
    var payload = {
      interaction_id: errorFeedbackInteractionId,
      source: source,
      source_domain: getSourceDomain(source),
      attempted_url: errorAttemptedUrl,
      error_type: errorErrorType,
      rating: "error_report",
      text: text || "",
      viewport: getViewport(),
      theme: settings.theme === "cream" ? "sepia" : settings.theme,
      timestamp: now
    };
    if (!errorFeedbackSubmitted) {
      payload.created_at = now;
    }
    payload.updated_at = now;

    fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(function () { /* silent */ });
  }

  // Radio selection: expand comment, update placeholder
  feedbackRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      sendFeedback(radio.value, "");
      if (feedbackSubmitted) {
        // Re-opening after submit: show form again
        feedbackThanks.classList.add("hidden");
        feedbackWidget.classList.remove("feedback-submitted");
      }
      feedbackExpand.classList.remove("hidden");
      // Context-sensitive placeholder
      if (radio.value === "up") {
        feedbackText.placeholder = "What worked well? (optional)";
      } else if (radio.value === "broken") {
        feedbackText.placeholder = "What happened? (optional)";
      } else {
        feedbackText.placeholder = "What went wrong? (optional)";
      }
    });
  });

  // Send button: submit and show confirmation
  feedbackSubmit.addEventListener("click", function () {
    var rating = getSelectedRating();
    if (!rating) return;
    var text = feedbackText.value.trim();
    sendFeedback(rating, text);
    feedbackSubmitted = true;
    feedbackExpand.classList.add("hidden");
    feedbackThanks.classList.remove("hidden");
    feedbackWidget.classList.add("feedback-submitted");
    feedbackText.value = "";
  });

  feedbackText.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      feedbackSubmit.click();
    }
  });

  // Update button: re-open for editing
  feedbackUpdateBtn.addEventListener("click", function () {
    feedbackThanks.classList.add("hidden");
    feedbackWidget.classList.remove("feedback-submitted");
    feedbackExpand.classList.remove("hidden");
    var rating = getSelectedRating();
    if (rating === "up") {
      feedbackText.placeholder = "What worked well? (optional)";
    } else if (rating === "broken") {
      feedbackText.placeholder = "What happened? (optional)";
    } else {
      feedbackText.placeholder = "What went wrong? (optional)";
    }
  });

  // --- Error feedback ---

  errorFeedbackToggle.addEventListener("click", function () {
    errorFeedbackToggle.classList.add("hidden");
    errorFeedbackForm.classList.remove("hidden");
    errorFeedbackText.focus();
  });

  errorFeedbackSubmit.addEventListener("click", function () {
    var text = errorFeedbackText.value.trim();
    sendErrorFeedback(text);
    errorFeedbackSubmitted = true;
    errorFeedbackForm.classList.add("hidden");
    errorFeedbackThanks.classList.remove("hidden");
    errorFeedbackText.value = "";
  });

  errorFeedbackText.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      errorFeedbackSubmit.click();
    }
  });

  // --- Try demo ---

  if (tryDemoBtn) {
    tryDemoBtn.addEventListener("click", function () {
      closeAllDropdowns();
      isDemoConversion = true;
      var demoUrl = "https://decant.cc/test-page";
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
