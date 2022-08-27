import { worker, contentScript } from "./common.js";

const items = {
  options: chrome.runtime.openOptionsPage,
  inject: worker.inject,
  comment: () => {
    contentScript.postComment("en", 100);
  },
};

async function init() {
  const showDev = await worker.getConfig('enableDevCommands');
  for (const key in items) {
    const elem = document.getElementById(key);
    if (elem.hasAttribute('dev') && !showDev)
      elem.style.display = "none";
    elem.onclick = () => {
      try {
        items[key]();
      } catch (err) {
        console.error("error in menu handler", err);
      }
    };
  }
}

init();
