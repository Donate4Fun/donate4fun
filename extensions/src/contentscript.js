import {
  worker,
  subscribe,
  cLog,
  sleep,
  pageScript,
  registerHandlers,
  donate,
  browser,
} from "./common.js";
import {
  waitLoaded,
  getButtons,
  postComment,
  isVideoLoaded,
  getVideoId,
  getChannelTitle,
  getChannelLogo,
} from "./youtube.js";

import {Bolt} from  "./dist/dff-bolt.js";

const buttonId = "donate4fun-button";

let bolt = null;

function init() {
  cLog("init");
  injectPageScript();
  window.addEventListener("yt-navigate-finish", load, true);
  window.addEventListener("yt-navigate-start", () => {
    bolt?.$destroy();
    bolt = null;
  }, true);

  registerHandlers({
    postComment,
    getVideoId,
    getChannelTitle,
    getChannelLogo,
    isVideoLoaded,
    sendPayment: pageScript.sendPayment,
    donate,
    onPaid: donation => { bolt?.onPaid(donation) },
  });

  browser.runtime.connect().onDisconnect.addListener(() => {
    bolt?.$destroy();
    bolt = null;
  });
}

async function load(evt) {
  cLog("Setting up...", evt);
  if (await waitLoaded(await worker.getConfig("checkInterval")))
    await patchButtons();
}

async function patchButtons() {
  if (!await worker.getConfig("enableBoltButton")) return;
  const buttons = getButtons();
  cLog("buttons", buttons);
  if (document.getElementById(buttonId) === null) {
    cLog("creating button");
    // Donate button could be already created after user navigated back to youtube video
    bolt = new Bolt({
      target: buttons,
      props: {
      },
      anchor: buttons.firstElementChild,
    });
  } else {
    cLog("button is already created");
  }
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

init();
