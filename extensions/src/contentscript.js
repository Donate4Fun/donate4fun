import {
  worker,
  subscribe,
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
  isLoaded,
} from "./youtube.js";
import cLog from "./log.js";
import Bolt from "./Bolt.svelte";

const buttonId = "donate4fun-button";

let bolt = null;

async function init() {
  cLog("init");
  await injectPageScript();
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
    ping: () => "pong",
  });

  cLog("connecting to background script");
  const port = browser.runtime.connect();
  port.onDisconnect.addListener(() => {
    cLog("onDisconnect", browser.runtime.lastError);
    bolt?.$destroy();
    bolt = null;
  });
  // Try to load instantly if extension was loaded while youtube was active
  if (isLoaded()) {
    cLog("Youtube is already loaded, patching");
    await patchButtons();
  }
  return "123";  // for easier debugging
}

async function load(evt) {
  cLog("Setting up...", evt);
  if (await waitLoaded(await worker.getConfig("checkInterval")))
    await patchButtons();
}

async function patchButtons() {
  if (!await worker.getConfig("enableBoltButton")) return;
  // Donate button could be already created after user navigated back to youtube video
  const button = document.getElementById(buttonId);
  if (button) {
    cLog("button is already created, destroying");
    button.remove();
  }
  const buttons = getButtons();
  cLog("creating button", buttons);
  bolt = new Bolt({
    target: buttons,
    props: {
    },
    anchor: buttons.firstElementChild,
  });
}

async function injectPageScript() {
  // page script is needed only for webln to work
  const scriptUrl = chrome.runtime.getURL('pagescript.js');
  cLog("injecting page script", scriptUrl);
  const scriptElement = document.createElement('script');
  scriptElement.src = scriptUrl;
  scriptElement.async = false;
  (document.head || document.documentElement).appendChild(scriptElement);
  await new Promise((resolve, reject) => {
    scriptElement.addEventListener("load", resolve);
  });
  cLog("page script loaded");
  const pong = await pageScript.ping();
  if (pong !== "pong")
    throw new Error("unexpected pong from page script", pong);
  cLog("page script responded");
}

const result = init();
export default result;  // return promise for executeScript to wait
