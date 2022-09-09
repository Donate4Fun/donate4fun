if (!window.donate4funPageScriptLoaded) {
  window.donate4funPageScriptLoaded = true;

  window.addEventListener("message", async (event) => {
    if (event.source !== window) return;
    if (event.data.type !== "donate4.fun-request") return;
    console.log("[dff] pageScript received event", event);
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
    console.log("[dff] pagescript responding with", message);
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
    console.log("webln.sendPayment result", result);
  }

  const handlers = {
    sendPayment: sendPayment,
  }
}
