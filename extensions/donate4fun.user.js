// ==UserScript==
// @name         Donate4.Fun
// @namespace    https://donate4.fun/
// @homepage     https://donate4.fun/
// @version      0.1
// @description  Donate4.Fun YouTube helper
// @author       nbryskin
// @match        *://*.youtube.com/*
// @exclude      *://music.youtube.com/*
// @exclude      *://*.music.youtube.com/*
// @icon64URL    https://stage.donate4.fun/static/D.svg
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @run-at       document-end
// @connect      donate4.fun
// @require      https://openuserjs.org/src/libs/sizzle/GM_config.js
// @downloadURL  https://github.com/Donate4Fun/donate4fun/raw/master/extensions/donate4fun.user.js
// @updateURL    https://github.com/Donate4Fun/donate4fun/raw/master/extensions/donate4fun.user.js
// @supportURL   https://github.com/donate4Fun/donate4fun/issues
// ==/UserScript==
/*global GM_config*/

const styles = `
#donate4fun-button {
  display: inline-block;
  --yt-button-icon-padding: 6px;
  color: var(--yt-spec-icon-inactive);
}
#donate4fun-button .flex-container {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding-right: var(--yt-button-icon-padding,8px);
}

#donate4fun-button .dff-icon {
  line-height: 1;
  padding: var(--yt-button-icon-padding,8px);
  width: var(--yt-button-icon-size,var(--yt-icon-width,40px));
  height: var(--yt-button-icon-size,var(--yt-icon-height,40px));
  color: var(--yt-button-color,inherit);
  background-color: transparent;
  text-transform: var(--yt-button-text-transform,inherit);
  display: inline-block;
  position: relative;
  box-sizing: border-box;
  font-size: 0;
}

#donate4fun-button .dff-text {
  color: var(--yt-button-icon-button-text-color,var(--yt-spec-text-secondary));
  font-size: var(--ytd-tab-system-font-size);
  font-weight: var(--ytd-tab-system-font-weight);
  letter-spacing: var(--ytd-tab-system-letter-spacing);
  text-transform: var(--ytd-tab-system-text-transform);
}

#donate4fun-button .dff-bolt {
  fill: var(--iron-icon-fill-color,currentcolor);
  stroke: var(--iron-icon-stroke-color,none);
}
`;

const donateButtonHtml = `
<div id="donate4fun-button">
  <div class=flex-container>
    <div class=dff-icon>
      <svg viewBox="60 60 160 160" xmlns="http://www.w3.org/2000/svg">
        <g>
          <path class=dff-bolt d="M79.7609 144.047L173.761 63.0466C177.857 60.4235 181.761 63.0466 179.261 67.5466L149.261 126.547H202.761C202.761 126.547 211.261 126.547 202.761 133.547L110.261 215.047C103.761 220.547 99.261 217.547 103.761 209.047L132.761 151.547H79.7609C79.7609 151.547 71.2609 151.547 79.7609 144.047Z" stroke-width="10"></path>
        </g>
      </svg>
    </div>
    <div class="dff-text">...</div>
  </div>
</div>
`;

let getButtons;
let unsubscribeVideoWS;

(() => {
  'use strict';
  GM_addStyle(styles);
  window.addEventListener("yt-navigate-finish", load, true);
  window.addEventListener("yt-navigate-start", () => {
    if (unsubscribeVideoWS) {
      unsubscribeVideoWS();
    }
  }, true);

  GM_config.init({
    id: 'donate4fun-config',
    title: "Donate4.Fun settings",
    fields: {
      defaultComment_en: {
        label: 'Default comment',
        type: 'text',
        size: 100,
        default: 'Hi! I like your video! I’ve donated you %amount% sats. You can take it on "donate 4 fun"'
      },
      defaultComment_ru: {
        label: 'Default comment RU',
        type: 'text',
        size: 100,
        default: 'Классное видео, спасибо! Задонатил тебе на "donate 4 fun"'
      },
      amount: {
        label: 'Amount (sats)',
        type: 'int',
        default: 100
      },
      enableComment: {
        label: 'Enable auto-comment',
        type: 'checkbox',
        default: true
      },
      _hunk: {
        label: "",
        type: "radio",
        options: [],
        section: ["Developer options", "This options are only for developers"],
      },
      apiHost: {
        label: 'API host (for testing)',
        type: 'text',
        default: 'donate4.fun'
      },
      checkInterval: {
        label: 'Check interval (ms)',
        type: 'int',
        default: 111
      }
    }
  });
  GM_registerMenuCommand("Settings", (event) => GM_config.open());
  GM_registerMenuCommand("Login", (event) => login());

  if (isMobile()) {
    getButtons = getButtons_mobile;
  } else if (isShorts()) {
    getButtons = getButtons_shorts;
  } else {
    getButtons = getButtons_main;
  }
})();

async function login() {
  const response = await apiGet("/lnauth");
  cLog("lnurl", response.lnurl);
}

function load(evt) {
  cLog("Setting up...", evt);
  //window.removeEventListener("yt-navigate-finish", load, true);
  checkLoaded();
}

function isShorts() {
  return location.pathname.startsWith("/shorts");
}

function isMobile() {
  return location.hostname == "m.youtube.com";
}

function checkLoaded() {
  const videoId = getVideoId();
  cLog('videoId', videoId);
  if (videoId === null) {
    cLog("it's not a video page, stop checking");
    return;
  }
  const is_shorts = isShorts();
  const offset_parent = getButtons()?.offsetParent;
  const is_video_loaded = isVideoLoaded();
  cLog(`Checking for load isShorts=${is_shorts} getButtons=${offset_parent} isVideoLoaded=${is_video_loaded}`);
  if (is_shorts || (offset_parent && is_video_loaded)) {
    patchButtons();
    cLog("Stopping check loop");
  } else {
    setTimeout(checkLoaded, GM_config.get('checkInterval'));
  }
}

async function patchButtons() {
  const buttons = getButtons();
  cLog("buttons", buttons);
  const placeholder = document.createElement("div");
  placeholder.innerHTML = donateButtonHtml;
  const node = placeholder.firstElementChild;
  buttons.insertBefore(node, buttons.children[0]);
  node.addEventListener("click", onDonateClick, true);
  const videoId = getVideoId();
  unsubscribeVideoWS = await subscribe(`youtube-video-by-vid:${videoId}`, (msg) => {
    cLog("youtube video updated", msg);
    fetchStats();
  });
  await fetchStats();
}

async function subscribe(topic, on_message) {
  const apiHost = GM_config.get('apiHost');
  const ws_uri = `wss://${apiHost}/api/v1/subscribe/${topic}`;
  const socket = new WebSocket(ws_uri);
  socket.onmessage = (event) => {
    cLog(`Message from ${topic}`, event);
    try {
      const msg = JSON.parse(event.data);
      on_message(msg);
    } catch (err) {
      console.error(`unexpected websocket ${topic} notification`, err, event);
    }
  };
  socket.onerror = (event) => {
    cLog(`WebSocket ${topic} error`, event);
    subscribe(topic, on_message);
  };
  let opened = true;
  socket.onclose = (event) => {
    cLog(`WebSocket ${topic} closed`, event);
    if (opened) {
      cLog(`WebSocket ${topic} reconnect`);
      subscribe(topic, on_message);
    }
  };
  await new Promise((resolve, reject) => {
    socket.onopen = _ => {
      cLog(`WebSocket ${topic} opened`);
      resolve();
    };
  });
  function unsubscribe() {
    opened = false;
    cLog(`Closing WebSocket ${topic}`);
    socket.close();
  }
  return unsubscribe;
}

async function apiGet(path) {
  const apiHost = GM_config.get('apiHost');
  const response = await fetch(`https://${apiHost}/api/v1/${path}`, {
    credentials: 'include',
  });
  return await response.json();
}

async function apiPost(path, data) {
  const apiHost = GM_config.get('apiHost');
  const response = await fetch(`https://${apiHost}/api/v1/${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data),
    credentials: 'include',
  });
  return await response.json();
}

async function fetchStats() {
  const totalDonatedNode = document.querySelector("#donate4fun-button .dff-text");
  const videoId = getVideoId();
  const videoInfo = await apiGet(`youtube-video/${videoId}`);
  cLog("video info", videoInfo);
  totalDonatedNode.innerText = videoInfo.total_donated;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitElement(id) {
  do {
    await sleep(100);
    const element = document.getElementById(id);
    if (element) {
      return element;
    }
  } while (true);
}

async function postComment(message) {
  // Scroll to comments section
  const comments = await waitElement("comments");
  comments.scrollIntoView({behavior: "smooth", block: "end"});

  // "Click" on a comment input placeholder
  const commentPlaceholder = await waitElement("simplebox-placeholder");
  commentPlaceholder.dispatchEvent(new Event("focus", {bubble: true}));

  const commentInput = await waitElement("contenteditable-root");
  commentInput.scrollIntoView({behavior: "smooth", block: "center"});

  // Enter comment text
  commentInput.textContent = message;
  commentInput.dispatchEvent(new Event('input', {bubbles: true}));
}

async function onDonateClick(evt) {
  const webln = unsafeWindow.webln;
  if (typeof(webln) === 'undefined') {
    showError("Install compatible Bitcoin Lightning wallet");
    return;
  }
  if (!webln.enabled) {
    // Show connect dialog
    await webln.enable();
  }
  const amount = GM_config.get("amount");
  // Make a donation
  const response = await apiPost('donate', {
    amount: amount,
    target: window.location.href
  });
  cLog("donate response", response);
  const videoLanguage = response.donation.youtube_video.default_audio_language;
  let defaultComment;
  try {
    defaultComment = GM_config.get(`defaultComment_${videoLanguage}`);
  } catch (exc) {
    defaultComment = GM_config.get("defaultComment_en");
  }
  let unsubscribeWs = await subscribe(`donation:${response.donation.id}`, async (msg) => {
    cLog("donation updated", msg);
    unsubscribeWs();
    if (GM_config.get("enableComment")) {
      await postComment(defaultComment.replace('%amount%', amount));
    }
  });
  const paymentRequest = response.payment_request;
  // Show payment dialog (or pay silently if budget allows)
  const paymentResult = await webln.sendPayment(paymentRequest);
  cLog("payment result", paymentResult);
}

function showError(message) {
  cLog(message);
}

function cLog() {
  arguments[0] = `[donate4fun] ${arguments[0]}`;
  console.log(...arguments);
}

function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  const height = innerHeight || document.documentElement.clientHeight;
  const width = innerWidth || document.documentElement.clientWidth;
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= height &&
    rect.right <= width
  );
}

function getButtons_shorts() {
  let elements = document.querySelectorAll(
    isMobile()
    ? "ytm-like-button-renderer"
    : "#like-button > ytd-like-button-renderer"
  );
  for (let element of elements) {
    if (isInViewport(element)) {
      return element;
    }
  }
}

function getButtons_mobile() {
  return document.querySelector(".slim-video-action-bar-actions");
}

function getButtons_main() {
  if (document.getElementById("menu-container")?.offsetParent === null) {
    return document.querySelector("ytd-menu-renderer.ytd-watch-metadata > div");
  } else {
    return document
      .getElementById("menu-container")
      ?.querySelector("#top-level-buttons-computed");
  }
}

function getVideoId() {
  const urlObject = new URL(window.location.href);
  const pathname = urlObject.pathname;
  if (pathname.startsWith("/clip")) {
    return document.querySelector("meta[itemprop='videoId']").content;
  } else {
    if (pathname.startsWith("/shorts")) {
      return pathname.slice(8);
    }
    return urlObject.searchParams.get("v");
  }
}

function isVideoLoaded() {
  if (isMobile()) {
    return document.getElementById("player").getAttribute("loading") == "false";
  }
  const videoId = getVideoId();

  return (
    document.querySelector(`ytd-watch-flexy[video-id='${videoId}']`) !== null
  );
}
