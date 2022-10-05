import browser from "webextension-polyfill";
import cLog from "./log.js";

async function callBackground(request) {
  cLog("sending to service worker", request);
  const response = await browser.runtime.sendMessage(request);
  cLog("received from service worker", response);
  if (response === undefined)
    throw browser.runtime.lastError;
  if (response.status === "error")
    throw new Error(response.error);
  return response.response;
}

const worker = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      return await callBackground({type: "donate4fun-request", command: prop, args: Array.from(arguments)});
    };
  }
});

async function getCurrentTab() {
  const queryOptions = { active: true, lastFocusedWindow: true };
  const [tab] = await browser.tabs.query(queryOptions);
  return tab;
}

function isSupportedPage(tab) {
  return tab?.url?.match('^https\:\/\/(www\.)?youtube\.com');
}

async function injectContentScript(tab) {
  if (browser.scripting) {
    cLog("injecting content script using browser.scripting", tab);
      function getTitle() {
        cLog("title", document.title);
      }
      const manifest = browser.runtime.getManifest();
      const contentScript = manifest.content_scripts[0];
      await browser.scripting.insertCSS({
        target: {tabId: tab.id},
        files: contentScript.css,
      });
      const injectionResults = await browser.scripting.executeScript({
        target: {tabId: tab.id},
        files: contentScript.js,
      });
      cLog("injection results", injectionResults, chrome.runtime.lastError);
      if (chrome.runtime.lastError)
        throw chrome.runtime.lastError;
  } else {
    cLog("injecting content script using browser.tabs", tab);
    await browser.tabs.executeScript({
      file: ['common.js'],
    });
  }
}

async function callTab(tab, func, args) {
  const msg = {
    type: "donate4fun-request",
    command: func,
    args: args,
  };
  cLog("sending to tab", tab, func, args, msg);
  const result = await browser.tabs.sendMessage(tab.id, msg);
  cLog("received from tab", tab, result);
  if (result.status === "error")
    throw new Error(result.message);
  else
    return result.response;
};

async function isConnectedToTab(tab) {
  try {
    if (await callTab(tab, "ping", []) === "pong")
      return true;
  } catch (error) {
    cLog("error while connecting to tab", tab, error);
  }
  return false;
}

let injectionPromise;

async function connectToPage() {
  cLog("connecting to contentScript");
  const tab = await getCurrentTab();
  if (!tab)
    throw new Error("No current tab");

  if (!isSupportedPage(tab))
    throw new Error("Page is not supported");

  if (!await isConnectedToTab(tab)) {
    cLog("error while sending to contentScript, injecting script and retrying", browser.runtime.lastError);
    if (!injectionPromise)
      injectionPromise = injectContentScript(tab);
    await injectionPromise;
    injectionPromise = null;
    cLog("content script injected, retrying");
    if (!await isConnectedToTab(tab))
      throw new Error("Failed to connect to tab: no ping");
  }

  const proxy = {
    get(obj, prop) {
      if (prop === 'then')
        return Reflect.get(...arguments);
      else
        return async function () {
          return await callTab(tab, prop, Array.from(arguments));
        };
    }
  };
  return new Proxy({}, proxy);
}

const pageScript = new Proxy({}, {
  get(obj, prop) {
    return async function () {
      const message = {
        type: "donate4.fun-request",
        method: prop,
        args: Array.from(arguments),
      };
      cLog("sending to pageScript", message);
      window.postMessage(message);
      return await new Promise((resolve, reject) => {
        async function handleResponse(event) {
          cLog("received from pageScript", event);
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

async function handleMessageWrapper(request, sendResponse) {
    const [moduleName, funcName] = request.command.split('.');
    const module = await import(moduleName);
    const func = module[funcName];
    sendResponse(await handleMessage(func, request.args));
}

function registerHandlers(handlers) {
  browser.runtime.onMessage.addListener((request, sender) => {
    if (request.type !== 'donate4fun-request')
      return false;
    const handler = handlers[request.command];
    if (!handler) {
      console.error(`Unexpected command ${request.command}`);
      return false;
    } else {
      return handleMessage(handler, request.args);
    }
  });
}

async function createWebsocket(topic, on_message, on_close) {
  const apiHost = await worker.getConfig('apiHost');
  const wsHost = apiHost.replace('http', 'ws');
  const socket = new WebSocket(`${wsHost}/api/v1/subscribe/${topic}`);
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function isTest() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.has('test');
}

async function createPopup(path) {
  const baseUrl = browser.runtime.getURL('popup.html');
  const window = await browser.windows.create({
    focused: true,
    url: `${baseUrl}#${path}`,
    type: "popup",
    width: 446,  // must match popup.html size
    height: 600,
  });
  cLog("opened popup", window);
}

async function waitElement(id) {
  let timeout = 3000;
  const step = 100;
  do {
    const element = document.getElementById(id);
    if (element)
      return element;
    if (timeout <= 0)
      throw new Error(`No such element #${id}`);
    await sleep(step);
    timeout -= step;
  } while (true);
}

function getStatic(filename) {
  return browser.runtime.getURL(`static/${filename}`);
}

async function apiPost(path, data) {
  return await worker.fetch("post", path, data);
}

async function donate(amount, target) {
  // Make a donation
  const response = await apiPost('donate', {
    amount: amount,
    target: target,
  });
  const donation = response.donation;
  if (donation.paid_at) {
    return donation;
  } else {
    return await new Promise(async (resolve, reject) => {
      // If donation is not paid using balance then try to use WebLN
      const unsubscribeWs = await subscribe(`donation:${donation.id}`, async (msg) => {
        unsubscribeWs();
        resolve(donation);
      });
      const paymentRequest = response.payment_request;
      // Show payment dialog (or pay silently if budget allows)
      try {
        await pageScript.sendPayment(paymentRequest);
      } catch (err) {
        reject(err);
      }
    });
  }
}

async function injectPageScript(filename) {
  const scriptUrl = chrome.runtime.getURL(filename);
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

export {
  worker,
  registerHandlers,
  browser,
  connectToPage,
  getCurrentTab,
  subscribe,
  sleep,
  isTest,
  pageScript,
  injectContentScript,
  createPopup,
  waitElement,
  getStatic,
  donate,
  injectPageScript,
};
