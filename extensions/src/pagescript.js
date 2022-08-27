window.addEventListener("message", async (event) => {
  if (event.source !== window) return;
  if (event.data.type !== "donate4.fun") return;
  console.log("donate4.fun event", event);
  if (event.data.method === 'webln.sendPayment') {
    if (!webln.enabled) {
      // Show connect dialog
      await webln.enable();
    }
    webln.sendPayment(...event.data.args);
  }
});
