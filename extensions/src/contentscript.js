import {
  worker,
  sleep,
  pageScript,
  registerHandlers,
  donate,
  browser,
  injectPageScript,
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
import cLog from "$lib/log.js";
import Bolt from "./Bolt.svelte";
import { apiOrigin } from "$lib/api.js";

const buttonId = "donate4fun-button";

let bolt = null;

function destroyBolt() {
  const button = document.getElementById(buttonId);
  if (button) {
    cLog("destroying bolt");
    button.remove();
  }
}

async function init() {
  cLog("Loading...");
  window.dispatchEvent(new CustomEvent("dff-unload"));
  // page script is needed only for webln to work
  await injectPageScript("webln.js");
  window.addEventListener("yt-navigate-finish", load, true);
  window.addEventListener("yt-navigate-start", destroyBolt, true);
  window.addEventListener("dff-unload", deinit, {once: true});

  registerHandlers({
    postComment,
    getVideoId,
    getChannelTitle,
    getChannelLogo,
    isVideoLoaded,
    sendPayment: pageScript.sendPayment,
    donate,
    onPaid: donation => { bolt?.onPaid(donation) },
    popupPath: () => "/youtube",
  });

  cLog("connecting to background script");
  const apiHost = await worker.getConfig("apiHost");
  apiOrigin.set(apiHost);
  // Try to load instantly if extension was loaded while youtube was active
  if (isLoaded()) {
    cLog("Youtube is already loaded, patching");
    await patchButtons(getButtons());
  }
  return "123";  // for easier debugging
}

async function deinit() {
  cLog("Unloading...");
  window.removeEventListener("yt-navigate-finish", load, true);
  window.removeEventListener("yt-navigate-start", destroyBolt, true);
  destroyBolt();
}

async function load(evt) {
  cLog("Setting up...", evt);
  const buttons = await waitLoaded(await worker.getConfig("checkInterval"));
  if (buttons)
    await patchButtons(buttons);
}

async function patchButtons(buttons) {
  if (!await worker.getConfig("enableBoltButton")) return;
  // Donate button could be already created after user navigated back to youtube video
  const oldButton = document.getElementById(buttonId);
  if (oldButton) {
    cLog("button is already created, destroying", oldButton);
    oldButton.remove();
  }
  cLog("creating button", buttons);
  const button = document.createElement('div');
  button.id = buttonId;
  buttons.insertBefore(button, buttons?.firstElementChild);

  cLog("creating bolt");
  const bolt_ = bolt = new Bolt({
    target: button,
    props: {},
  });

  // Observer self-removal
  new MutationObserver(function (mutations) {
    cLog("mutations", mutations);
    if (mutations[0].removedNodes[0] === button) {
      cLog("removal observed");
      bolt = null;
      bolt_.$destroy();
      this.disconnect();
    }
  }).observe(buttons, {childList: true});
}

const result = init();
export default result;  // return promise for executeScript to wait
