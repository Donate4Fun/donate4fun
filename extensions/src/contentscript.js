import { registerHandlers, worker } from "./common.js";

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
    <div class="dff-text dff-loading">…</div>
  </div>
</div>
`;
const buttonId = "donate4fun-button";

let getButtons;
let unsubscribeVideoWS;
let isCommentPosted;
let checkIntervalId;
let unsafeWindow;

function showError(message) {
  cLog(message);
}

function cLog() {
  arguments[0] = `[donate4fun] ${arguments[0]}`;
  console.log(...arguments);
}

function init() {
  cLog("init");
  injectPageScript();
  registerHandlers({
    postComment: postComment,
  });
  if (isMobile()) {
    getButtons = getButtons_mobile;
  } else if (isShorts()) {
    getButtons = getButtons_shorts;
  } else {
    getButtons = getButtons_main;
  }
  checkLoaded();
  window.addEventListener("yt-navigate-finish", load, true);
  window.addEventListener("yt-navigate-start", () => {
    if (unsubscribeVideoWS) {
      unsubscribeVideoWS();
    }
  }, true);
}

async function load(evt) {
  cLog("Setting up...", evt);
  isCommentPosted = false;
  checkIntervalId = setInterval(checkLoaded, await worker.getConfig("checkInterval"));
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
    clearInterval(checkIntervalId);
    return;
  }
  const is_shorts = isShorts();
  const offset_parent = getButtons()?.offsetParent;
  const is_video_loaded = isVideoLoaded();
  cLog(`Checking for load isShorts=${is_shorts} getButtons=${offset_parent} isVideoLoaded=${is_video_loaded}`);
  if (is_shorts || (offset_parent && is_video_loaded)) {
    patchButtons();
    cLog("Stopping check loop");
    clearInterval(checkIntervalId);
  }
}

async function patchButtons() {
  const buttons = getButtons();
  cLog("buttons", buttons);
  if (document.getElementById(buttonId) === null) {
    cLog("creating button");
    // Donate button could be already created after user navigated back to youtube video
    const placeholder = document.createElement("div");
    placeholder.id = buttonId;
    const parser = new DOMParser();
    const parsed = parser.parseFromString(donateButtonHtml, `text/html`);
    placeholder.appendChild(parsed.body.firstChild);
    const node = placeholder.firstElementChild;
    buttons.insertBefore(node, buttons.children[0]);
  } else {
    cLog("button is already created");
  }
  const node = buttons.children[0];
  node.removeEventListener("click", onDonateClick, true);
  node.addEventListener("click", onDonateClick, true);
  const videoId = getVideoId();
  unsubscribeVideoWS = await subscribe(`youtube-video-by-vid:${videoId}`, (msg) => {
    cLog("youtube video updated", msg);
    fetchStats();
  });
  await fetchStats();
}

async function createWebsocket(topic, on_message, on_close) {
  const apiHost = await worker.getConfig('apiHost');
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
  };
  socket.onclose = (event) => {
    cLog(`WebSocket ${topic} closed`, event);
    on_close();
  };
  return socket;
}

async function subscribe(topic, on_message) {
  let opened = true;
  let socket = null;
  let delay = 1000;
  async function onClose() {
    if (opened) {
      cLog(`WebSocket ${topic} closed, reconnecting in ${delay}ms`);
      await sleep(delay);
      if (delay < 30000)
        delay = delay * 1.5;
      socket = await createWebsocket(topic, on_message, onClose);
    }
  }
  function unsubscribe() {
    opened = false;
    cLog(`Closing WebSocket ${topic}`);
    socket.close();
  }
  socket = await createWebsocket(topic, on_message, onClose);
  await new Promise((resolve, reject) => {
    socket.onopen = _ => {
      cLog(`WebSocket ${topic} opened`);
      resolve();
    };
  });
  return unsubscribe;
}

async function fetchStats() {
  const totalDonatedNode = document.querySelector("#donate4fun-button .dff-text");
  const videoId = getVideoId();
  const videoInfo = await apiGet(`youtube-video/${videoId}`);
  cLog("video info", videoInfo);
  totalDonatedNode.innerText = videoInfo.total_donated;
  totalDonatedNode.classList.remove("dff-loading");
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitElement(id) {
  let timeout = 3000;
  const step = 100;
  do {
    const element = document.getElementById(id);
    if (element)
      return element;
    if (timeout <= 0)
      throw new Error(`No such element #${id}`);
    await sleep(step);
    timeout -= step;
  } while (true);
}

async function postComment(language, amount) {
  if (isCommentPosted) return;

  let defaultComment;
  try {
    defaultComment = await worker.getConfig(`defaultComment_${language}`);
  } catch (exc) {
    defaultComment = await worker.getConfig("defaultComment_en");
  }

  defaultComment.replace('%amount%', amount);

  // Scroll to comments section
  const comments = await waitElement("comments");
  comments.scrollIntoView({behavior: "smooth"});

  // "Click" on a comment input placeholder
  const commentPlaceholder = await waitElement("simplebox-placeholder");
  commentPlaceholder.scrollIntoView({behavior: "smooth"});
  commentPlaceholder.click();
  //commentPlaceholder.dispatchEvent(new Event("focus", {bubble: true}));

  const commentInput = await waitElement("contenteditable-root");
  commentInput.scrollIntoView({behavior: "smooth", block: "center"});

  // Enter comment text
  commentInput.dispatchEvent(new Event('focus', {bubbles: true}));
  commentInput.textContent = defaultComment;
  // Thanks to https://github.com/keepassxreboot/keepassxc-browser/blob/d7e34662637b869500e8bb6344cdd642c2fb079b/keepassxc-browser/content/keepassxc-browser.js#L659-L663
  commentInput.dispatchEvent(new Event('input', {bubbles: true}));
  commentInput.dispatchEvent(new Event('change', {bubbles: true}));
  commentInput.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: false, key: '', char: '' }));
  commentInput.dispatchEvent(new KeyboardEvent('keypress', { bubbles: true, cancelable: false, key: '', char: '' }));
  commentInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, cancelable: false, key: '', char: '' }));

  const submitButton = await waitElement('submit-button');
  cLog("patching click for", submitButton);
  submitButton.addEventListener("click", () => {
    cLog("comment posted");
    isCommentPosted = true;
  }, true);
}

function injectPageScript() {
  // page script is needed only for webln to work
  const scriptUrl = chrome.runtime.getURL('src/pagescript.js');
  cLog("scriptUrl", scriptUrl);
  const scriptElement = document.createElement('script');
  scriptElement.setAttribute("src", scriptUrl);
  (document.head || document.documentElement).appendChild(scriptElement);
  window.postMessage({type: "donate4.fun", test: "test"});
}

function sendPayment(paymentRequest) {
  window.postMessage({
    type: "donate4.fun",
    method: "webln.sendPayment",
    args: [paymentRequest],
  });
}

async function getUnsafeWindow() {
  // inject code into "the other side" to talk back to this side;
  const scriptElement = document.createElement('script');
  //appending text to a function to convert it's src to string only works in Chrome
  scriptElement.textContent = '(' + function () { 
    const event = new CustomEvent("dffevent", {detail: {passback: window}});
    window.addEventListener('dffevent', (e) => console.log(e));
    window.dispatchEvent(event);
  } + ')();';
  const promise = new Promise((resolve, reject) => {
    window.addEventListener("dffevent", e => {
      resolve(e.detail.passback);
    });
  });
  //cram that sucker in 
  (document.head || document.documentElement).appendChild(scriptElement);
  //and then hide the evidence as much as possible.
  //scriptElement.parentNode.removeChild(scriptElement);
  //now listen for the message
  unsafeWindow = await promise;
}

async function onDonateClick(evt) {
  const boltElement = document.querySelector("#donate4fun-button .dff-icon");
  boltElement.classList.add("dff-icon-animate");
  const amount = await worker.getConfig("amount");
  // Make a donation
  const response = await apiPost('donate', {
    amount: amount,
    target: window.location.href
  });
  cLog("donate response", response);
  let unsubscribeWs = await subscribe(`donation:${response.donation.id}`, async (msg) => {
    cLog("donation updated", msg);
    unsubscribeWs();
    boltElement.classList.remove("dff-icon-animate");
    if (await worker.getConfig("enableComment")) {
      const videoLanguage = response.donation.youtube_video.default_audio_language;
      await postComment(videoLanguage, amount);
    }
  });
  const paymentRequest = response.payment_request;
  // Show payment dialog (or pay silently if budget allows)
  sendPayment(paymentRequest);
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

async function apiPost(path, data) {
  return await worker.fetch("post", path, data);
}

async function apiGet(path) {
  return await worker.fetch("get", path);
}

init();
