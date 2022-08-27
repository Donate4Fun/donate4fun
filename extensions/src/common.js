const browser = globalThis.browser || globalThis.chrome;

async function callBackground(request) {
  console.log("sending to service worker", request);
  return await new Promise((resolve, reject) => {
    browser.runtime.sendMessage(request, response => {
      console.log("response from service worker", response);
      if (response === undefined) {
        reject(browser.runtime.lastError);
      } else if (response.status === "error") {
        // TODO: use something like serialize-error
        reject(new Error(response.error));
      } else {
        resolve(response.response);
      }
    });
  });
}

const worker = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      return await callBackground({command: prop, args: Array.from(arguments)});
    };
  }
});

async function getCurrentTab() {
  const queryOptions = { active: true, lastFocusedWindow: true };
  // `tab` will either be a `tabs.Tab` instance or `undefined`.
  // NOTE: chrome.tabs.query doesn't work here - it returns undefined
  const [tab] = await browser.tabs.query(queryOptions);
  if (tab === undefined)
    throw new Error("could not find current tab");
  return tab;
}

const contentScript = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      const tab = await getCurrentTab();
      const msg = {command: prop, args: Array.from(arguments)};
      console.log("sending to tab", tab, msg);
      return await browser.tabs.sendMessage(tab.id, msg);
    };
  }
});

async function handleMessage(handler, args) {
  try {
    const response = await handler(...args);
    return {status: "success", response: response};
  } catch (error) {
    console.error(`error in handler ${handler}`, error);
    return {
      status: "error",
      error: error.toString(),
      message: error.message,
      stack: error.stack,
    };
  }
}

async function registerHandlers(handlers) {
  browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const handler = handlers[request.command];
    if (!handler) {
      console.error(`Unexpected command ${request.command}`);
      return false;
    } else {
      handleMessage(handler, request.args).then(sendResponse);
      return true;
    }
  });
}

export {
  worker,
  registerHandlers,
  browser,
  contentScript,
};
