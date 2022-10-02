import cLog from "./log.js";

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

  async function sendPayment(request) {
    if (!window.webln)
      throw new Error("No webln found");
    if (!webln.enabled) {
      // Show connect dialog
      await webln.enable();
    }
    const result = await webln.sendPayment(request);
    cLog("webln.sendPayment result", result);
  }

  async function emulateKeypresses(selector) {
    const element = document.querySelector(selector);
    // Thanks to https://github.com/keepassxreboot/keepassxc-browser/blob/d7e34662637b869500e8bb6344cdd642c2fb079b/keepassxc-browser/content/keepassxc-browser.js#L659-L663
    // This code is here because if call it from content script warnings will occur "Permission denied to access property X". (YouTube overrides event handles and tries to access event attributes)
    element.dispatchEvent(new Event('input', {bubbles: true}));
    element.dispatchEvent(new Event('change', {bubbles: true}));
    element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: false, key: '', char: '' }));
    element.dispatchEvent(new KeyboardEvent('keypress', { bubbles: true, cancelable: false, key: '', char: '' }));
    element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, cancelable: false, key: '', char: '' }));
  }

  const handlers = {
    sendPayment,
    emulateKeypresses,
    ping: () => "pong",
  }
} else {
  cLog("page script already loaded");
}
