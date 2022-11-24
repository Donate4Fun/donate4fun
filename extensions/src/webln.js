import cLog from "$lib/log.js";
import { sendPayment } from "$lib/utils.js";

if (!window.donate4funPageScriptLoaded) {
  window.donate4funPageScriptLoaded = true;
  cLog("loading page script");

  window.addEventListener("message", async (event) => {
    if (event.source !== window) return;
    if (event.data.type !== "donate4.fun-request") return;
    cLog("[dff] pageScript received event", event);
    const handler = handlers[event.data.method];
    let message;
    try {
      const result = await handler(...event.data.args);
      message = {
        type: "donate4.fun-response",
        result: result,
      };
    } catch (err) {
      message = {
        type: "donate4.fun-exception",
        error: err,
      };
    }
    cLog("[dff] pagescript responding with", message);
    window.postMessage(message);
  });

  async function emulateKeypresses(selector, content) {
    const element = selector === ':focus' ? document.activeElement : document.querySelector(selector);
    // This code is here because if call it from content script warnings will occur "Permission denied to access property X". (YouTube overrides event handles and tries to access event attributes)
    // This works on Chrome
    const dataTransfer = new DataTransfer();
    dataTransfer.setData("text/plain", content);
    element.dispatchEvent(new ClipboardEvent('paste', { bubbles: true, clipboardData: dataTransfer, data: null }));
    // And this works on Firefox
    element.dispatchEvent(new InputEvent('beforeinput', {bubbles: true, inputType: "insertText", data: content}));
    element.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: "insertText", data: content}));
    element.dispatchEvent(new Event('change', {bubbles: true}));
  }

  const handlers = {
    sendPayment,
    emulateKeypresses,
    ping: () => "pong",
  }
} else {
  cLog("page script already loaded");
}
