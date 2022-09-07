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
      const result = await browser.tabs.sendMessage(tab.id, msg);
      console.log("received from tab", tab, result);
      return result.response;
    };
  }
});

async function handleMessage(handler, args) {
  try {
    const response = (handler.constructor.name === 'AsyncFunction') ? await handler(...args) : handler(...args);
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

async function createWebsocket(topic, on_message, on_close) {
  const apiHost = await worker.getConfig('apiHost');
  const ws_uri = `wss://${apiHost}/api/v1/subscribe/${topic}`;
  const socket = new WebSocket(ws_uri);
  socket.onmessage = (event) => {
    cLog(`Message from ${topic}`, event);
    try {
      const msg = JSON.parse(event.data);
      on_message(msg);
    } catch (err) {
      console.error(`unexpected websocket ${topic} notification`, err, event);
    }
  };
  socket.onerror = (event) => {
    cLog(`WebSocket ${topic} error`, event);
  };
  socket.onclose = (event) => {
    cLog(`WebSocket ${topic} closed`, event);
    on_close();
  };
  return socket;
}

async function subscribe(topic, on_message) {
  let opened = true;
  let socket = null;
  let delay = 1000;
  async function onClose() {
    if (opened) {
      cLog(`WebSocket ${topic} closed, reconnecting in ${delay}ms`);
      await sleep(delay);
      if (delay < 30000)
        delay = delay * 1.5;
      socket = await createWebsocket(topic, on_message, onClose);
    }
  }
  function unsubscribe() {
    opened = false;
    cLog(`Closing WebSocket ${topic}`);
    socket.close();
  }
  socket = await createWebsocket(topic, on_message, onClose);
  await new Promise((resolve, reject) => {
    socket.onopen = _ => {
      cLog(`WebSocket ${topic} opened`);
      resolve();
    };
  });
  return unsubscribe;
}

function cLog() {
  arguments[0] = `[donate4fun] ${arguments[0]}`;
  console.log(...arguments);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export {
  worker,
  registerHandlers,
  browser,
  contentScript,
  getCurrentTab,
  subscribe,
  cLog,
  sleep,
};
