import {worker, waitElement, sleep, pageScript} from "$extlib/common.js";
import cLog from "$lib/log.js";

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
  const elements = document.querySelectorAll(
    isMobile()
    ? "ytm-like-button-renderer"
    : "#like-button > ytd-like-button-renderer"
  );
  for (const element of elements)
    if (isInViewport(element))
      return element;
}

function getButtons_mobile() {
  return document.querySelector(".slim-video-action-bar-actions");
}

function getButtons_main() {
  if (document.getElementById("menu-container")?.offsetParent === null) {
    // Patching this element causes errors in console on window resize
    return document.querySelector("ytd-menu-renderer.ytd-watch-metadata > div");
  } else {
    return document
      .getElementById("menu-container")
      ?.querySelector("#top-level-buttons-computed");
  }
}

function getVideoId(url) {
  url = url || window.location.href;
  const urlObject = new URL(url);
  const pathname = urlObject.pathname;
  if (pathname.startsWith("/clip")) {
    return document.querySelector("meta[itemprop='videoId']").content;
  } else if (pathname.startsWith("/shorts")) {
    return pathname.slice(8);
  } else {
    return urlObject.searchParams.get("v");
  }
}

function getParent() {
  return isShorts()
    ? document.querySelector("ytd-player#player").parentElement.parentElement
    : document.querySelector("ytd-video-owner-renderer");
}

function getChannelLogo() {
  if (isVideoPage())
    return getParent().querySelector("#avatar > img").src;
  else if (isChannelPage())
    return document.querySelector('#channel-container #avatar img').src;
}

function getChannelTitle() {
  if (isVideoPage())
    return getParent().querySelector("#channel-name a").textContent;
  else if (isChannelPage())
    return document.querySelector("#channel-container #text.ytd-channel-name").textContent;
}

function getChannelId() {
  if (isVideoPage())
    return getParent().querySelector("#channel-name a").href;
  else {
    if (location.pathname.startsWith('/channel/'))
      return location.pathname.split('/')[2];

    const snippetLink = document.querySelector('#snippet a[href^="/channel/"]');
    if (snippetLink)
      return snippetLink.href;

    // This tag contains valid ID only when after loading the whole page
    // After doesn't change afrer navigation, so it could be invalid
    return document.querySelector('meta[itemprop="channelId"]')?.content;
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

function isVideoPage() {
  return location.pathname === '/watch' || location.pathname.startsWith('/shorts/');
}

function getCanonicalLocation() {
  const canonical = document.querySelector('link[rel="canonical"]').href;
  return canonical && new URL(canonical);
}

function isChannelPage() {
  // FIXME: Check for more YouTube's own paths here
  return location.pathname !== '/' && (
    location.pathname.startsWith('/c/') || location.pathname.startsWith('/channel/') || !!getChannelId()
  );
}

function isShorts() {
  return location.pathname.startsWith("/shorts");
}

function isMobile() {
  return location.hostname === "m.youtube.com";
}

function getButtons() {
  if (isMobile()) {
    return getButtons_mobile();
  } else if (isShorts()) {
    return getButtons_shorts();
  } else {
    return getButtons_main();
  }
}

async function waitLoaded(checkInterval) {
  const videoId = getVideoId();
  cLog('videoId', videoId);
  if (videoId === null) {
    cLog("it's not a video page, stop checking");
    return false;
  }
  const is_shorts = isShorts();

  while (true) {
    const buttons = getButtons();//?.offsetParent;
    const is_video_loaded = isVideoLoaded();
    cLog(`Checking for load isShorts=${is_shorts} getButtons=${buttons} isVideoLoaded=${is_video_loaded}`);
    if ((is_shorts || is_video_loaded) && buttons)
      return buttons;
    await sleep(checkInterval);
  }
}

function isLoaded() {
  const offset_parent = getButtons();//?.offsetParent;
  return (isShorts() && getButtons()) || (offset_parent && isVideoLoaded());
}

function isCommentEnabled() {
  const comments = document.getElementById("comments");
  return comments.offsetParent !== null;
}

async function postComment(language, amount) {
  cLog("posting comment", language, amount);
  let comment;
  try {
    comment = await worker.getConfig(`defaultComment_${language}`);
  } catch (exc) {
    comment = await worker.getConfig("defaultComment");
  }

  comment.replace('%amount%', amount);

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
  //commentInput.dispatchEvent(new Event('focus', {bubbles: true}));
  commentInput.textContent = comment;
  await pageScript.emulateKeypresses("#contenteditable-root");

  const pattern = /^.+!/g;
  const selection = window.getSelection();
  const textNode = commentInput.childNodes[0];
  let match;
  selection.removeAllRanges();
  while (match = pattern.exec(comment)) {
    // Select customizable part of text
    const range = document.createRange();
    range.setStart(textNode, match.index);
    range.setEnd(textNode, pattern.lastIndex);
    selection.addRange(range);
  }
  commentInput.focus();

  const submitButton = await waitElement('submit-button');
  cLog("patching click for", submitButton);
  return new Promise((resolve, reject) => {
    submitButton.addEventListener("click", () => {
      cLog("comment posted");
      resolve();
    }, true);
  });
}

export {
  isVideoLoaded,
  getChannelLogo,
  getChannelTitle,
  getVideoId,
  getChannelId,
  isInViewport,
  waitLoaded,
  getButtons,
  postComment,
  isCommentEnabled,
  isLoaded,
  isShorts,
  isVideoPage,
  isChannelPage,
}
