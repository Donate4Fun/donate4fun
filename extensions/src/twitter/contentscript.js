import Bolt from "./Bolt.svelte";
import { cLog, cError } from "$lib/log.js";
import { registerHandlers, injectPageScript, worker, donate } from "$extlib/common.js";
import { apiOrigin } from "$lib/api.js";
import { getCurrentAccountHandle } from "./twitter.js";

const buttonClass = "donate4fun";
let observer;
let pageBolt;

async function init() {
  cLog("loading");
  await injectPageScript("webln.js");
  registerHandlers({
    getTweetInfo,
    getAuthorInfo,
    isTweetPage,
    isAuthorPage,
    getCurrentAccountHandle,
    donate,
    onPaid: (donation) => {
      if ((isTweetPage() || isAuthorPage()) && pageBolt)
        pageBolt.onPaid(donation);
      else
        cError("Current page is not a Tweet page");
    },
    popupPath: () => "/twitter",
  });
  const apiHost = await worker.getConfig("apiHost");
  apiOrigin.set(apiHost);
 
  if (isAuthorPage())
    patchAuthor();
  patchTweets();
  observer = observe();
}

function getUrl() {
  return window.location.href;
}

function isTweetPage() {
  const tweetUrl = getUrl();
  // location.href could be wrong if tweet editor is open
  return /^https:\/\/twitter.com\/\w+\/status\/\d+/.test(tweetUrl);
}

const profileUrlRegexp = /^https:\/\/twitter.com\/(?!home|messages|notifications|settings)(?<username>[a-zA-Z0-9_]{4,15})($|\/.*)/;

function isAuthorPage() {
  return profileUrlRegexp.test(getUrl());
}

function getTweetInfo() {
  const pageUrl = getUrl();
  const tweetUrlPath = new URL(pageUrl).pathname;
  const tweetAnchor = document.querySelector(`article[data-testid="tweet"] a[href="${tweetUrlPath}"]`);
  const allTweets = document.querySelectorAll('article[data-testid="tweet"]');
  const tweetElement = [...allTweets].filter(tweet => tweet.contains(tweetAnchor))[0];
  const avatar = tweetElement?.querySelector('div[data-testid="Tweet-User-Avatar"]');
  const authorUrl = avatar?.querySelector('a')?.href;
  const authorAvatar = avatar?.querySelector('img')?.src;
  const authorName = tweetElement?.querySelector('div[data-testid="User-Names"] a')?.innerHtml;
  return {
    pageUrl,
    authorUrl,
    authorAvatar,
    authorName,
  };
}

function getAuthorInfo() {
  const pageUrl = getUrl();
  const authorHandle = pageUrl.match(profileUrlRegexp)?.groups.username;
  const authorAvatar = document.querySelector(`[data-testid='UserAvatar-Container-${authorHandle}'] a[href='/${authorHandle}/photo'] img`)?.src;
  const authorName =  document.querySelector("[data-testid='UserName'] span")?.innerHTML;
  return {
    pageUrl,
    authorHandle,
    authorAvatar,
    authorName,
  };
}

async function patchAuthor() {
  const userActionsButton = document.querySelector('[data-testid="userActions"]');
  if (userActionsButton === null) {
    cError("Can find userActions, unable to patch author");
    return;
  }
  const buttons = userActionsButton.parentElement;
  const existingButtons = buttons.querySelectorAll(`.${buttonClass}`);
  for (const existingButton of existingButtons)
    existingButton.remove();
  const boltButton = document.createElement('div');
  boltButton.className = buttonClass;
  boltButton.style.display = 'contents';
  buttons.insertBefore(boltButton, userActionsButton);
  const pageUrl = getUrl();
  cLog("patching author", pageUrl);
  const bolt = new Bolt({
    target: boltButton,
    props: {
      pageUrl,
      isTweet: false,
    },
  });
  cLog("Updating current pageBolt to", bolt);
  pageBolt = bolt;
}

async function patchTweets() {
  const tweets = document.querySelectorAll('article');
  for (const tweet of tweets)
    patchTweet(tweet);
}

async function patchTweet(tweet) {
  const likeButton = tweet.querySelector('div[role="button"][data-testid$="like"]');
  if (likeButton === null)
    return;
  const buttons = likeButton.parentElement.parentElement;
  const existingButtons = buttons.querySelectorAll(`.${buttonClass}`);
  for (const existingButton of existingButtons)
    existingButton.remove();
  const boltButton = document.createElement('div');
  boltButton.className = buttonClass;
  boltButton.style.display = 'contents';
  buttons.insertBefore(boltButton, likeButton.parentElement.nextSibling);
  const anchor = tweet.querySelector('a[href*="/status/"]');
  let tweetUrl;
  if (anchor !== null)
    tweetUrl = anchor.href;
  else if (isTweetPage())
    tweetUrl = getUrl();
  else {
    cLog("Tweet has no url nor this is tweet page", tweet);
    return;
  }
  cLog("patching tweet", tweet, tweetUrl);
  const bolt = new Bolt({
    target: boltButton,
    props: {
      tweetUrl,
      isTweet: true,
    },
  });
  if (isTweetPage() && tweetUrl === getUrl()) {
    cLog("Updating current pageBolt to", bolt);
    pageBolt = bolt;
  }
}

function observe() {
  const observer = new MutationObserver((mutations, observer) => {
    try {
      for (const mutation of mutations) {
        for (const addedNode of mutation.addedNodes) {
          if (addedNode.nodeType !== 1) // ELEMENT_NODE
            continue;
          if (isAuthorPage() && addedNode.querySelector('[data-testid="userActions"]'))
            patchAuthor();
          if (addedNode.querySelectorAll('article').length === 1)
            patchTweet(addedNode.querySelector('article'));
        }
      }
    } catch (err) {
      cLog("error in mutation observer", err);
    }
  });
  observer.observe(document, {
    subtree: true,
    childList: true,
  });
  return observer;
}


const result = init();
export default result;  // return promise for executeScript to wait
