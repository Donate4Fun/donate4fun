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

async function injectContentScript() {
  const tab = await getCurrentTab();
  console.log("injecting to", tab);
  if (chrome.scripting) {
    return await new Promise((resolve, reject) => {
      function getTitle() {
        console.log("title", document.title);
      }
      // Chrome Mv3
      chrome.scripting.executeScript({
        target: {tabId: tab.id},
        files: ["src/contentscript_loader.js"],
      }, (injectionResults) => {
        console.log("injection result", injectionResults, chrome.runtime.lastError);
        if (chrome.runtime.lastError)
          reject(chrome.runtime.lastError);
        else {
          for (const frameResult of injectionResults)
            console.log('Frame Title: ' + frameResult.result);
          resolve();
        }
      });
    });
  } else {
    await browser.tabs.executeScript({
      file: ['/common.js'],
    });
  }
}

const contentScript = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      const tab = await getCurrentTab();
      const msg = {command: prop, args: Array.from(arguments)};
      console.log("sending to tab", tab, msg);
      let result;
      try {
        result = await browser.tabs.sendMessage(tab.id, msg);
      } catch (err) {
        console.log("[dff] error while sending to contentScript, injecting script and retrying", err);
        await injectContentScript();
        result = await browser.tabs.sendMessage(tab.id, msg);
      }
      console.log("received from tab", tab, result);
      if (result.status === "error")
        throw new Error(result.message);
      else
        return result.response;
    };
  }
});

const pageScript = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      const message = {
        type: "donate4.fun-request",
        method: prop,
        args: Array.from(arguments),
      };
      console.log("sending to pageScript", message);
      window.postMessage(message);
      return await new Promise((resolve, reject) => {
        async function handleResponse(event) {
          console.log("received from pageScript", event);
          if (event.source !== window)
            return;
          if (event.data.type === "donate4.fun-response") {
            window.removeEventListener("message", handleResponse);
            resolve(event.data.result);
          } else if (event.data.type === "donate4.fun-exception") {
            window.removeEventListener("message", handleResponse);
            reject(event.data.error);
          }
        }
        window.addEventListener("message", handleResponse);
      });
    };
  }
});

async function handleMessage(handler, args) {
  try {
    const response = (handler.constructor.name === 'AsyncFunction') ? await handler(...args) : handler(...args);
    return {status: "success", response: response};
  } catch (error) {
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

function isTest() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.has('test');
}

async function createPopup() {
  const window = await new Promise((resolve, reject) => {
    browser.windows.create({
      focused: true,
      url: browser.runtime.getURL('src/window.html'),
      type: "popup",
      width: 400,
      height: 600,
    }, (window) => {
      resolve(window);
    });
  });
  console.log("opened popup", window);
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
  isTest,
  pageScript,
  injectContentScript,
  createPopup,
};
