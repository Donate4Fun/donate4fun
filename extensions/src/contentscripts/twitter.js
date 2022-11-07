import TwitterBolt from "../TwitterBolt.svelte";
import cLog from "$lib/log.js";
import { registerHandlers } from "../common.js";

const buttonClass = "donate4fun";
let observer;

async function init() {
  cLog("loading");
  registerHandlers({
    getTweetInfo,
    popupPath: () => "/twitter",
  });
 
  patchTweets();
  observer = observe();
}

function getTweetInfo() {
  const tweetUrl = location.href;
  const avatar = document.querySelector('div[data-testid="Tweet-User-Avatar"]');
  const authorUrl = avatar?.querySelector('a')?.href;
  const authorAvatar = avatar?.querySelector('img')?.src;
  const authorName = document?.querySelector('div[data-testid="User-Names"] a')?.textContent;
  return {
    tweetUrl,
    authorUrl,
    authorAvatar,
    authorName,
  };
}

async function patchTweets() {
  const tweets = document.querySelectorAll('article');
  for (const tweet of tweets)
    patchTweet(tweet);
}

async function patchTweet(tweet) {
  cLog("patching tweet", tweet);
  const likeButton = tweet.querySelector('div[role="button"][data-testid$="like"]');
  if (likeButton === null)
    return;
  const buttons = likeButton.parentElement.parentElement;
  const existingButtons = buttons.querySelectorAll(`.${buttonClass}`);
  for (const existingButton of existingButtons)
    existingButton.remove();
  const boltButton = document.createElement('div');
  boltButton.className = buttonClass;
  buttons.insertBefore(boltButton, likeButton.parentElement.nextSibling);
  const anchor = tweet.querySelector('a[dir="auto"]');
  if (anchor === null)
    return;
  const bolt = new TwitterBolt({
    target: boltButton,
    props: {
      tweetUrl: anchor.href,
    },
  });
}

function observe() {
  const observer = new MutationObserver((mutations, observer) => {
    try {
      for (const mutation of mutations) {
        for (const addedNode of mutation.addedNodes) {
          if (addedNode.nodeType !== 1) // ELEMENT_NODE
            continue;
          const tweet = addedNode.querySelector('article');
          if (tweet)
            patchTweet(addedNode)
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
