import browser from "webextension-polyfill";
import { cLog, cError } from "$lib/log.js";
import { subscribe } from "$lib/api.js";

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

async function injectContentScript(tab, contentScript) {
  cLog("injecting content script using browser.scripting", tab.url, contentScript);
  if (contentScript.css)
    await browser.scripting.insertCSS({
      target: {tabId: tab.id},
      files: contentScript.css,
    });
  const injectionResults = await browser.scripting.executeScript({
    target: {tabId: tab.id},
    files: contentScript.js,
  });
  cLog("injection results", injectionResults);
  for (const result of injectionResults)
    if (result.error)
      console.error("error while injecting contentscript", result.error, tab, contentScript);
  if (browser.runtime.lastError)
    throw browser.runtime.lastError;
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
  if (result.status === "error") {
    const error = new Error(result.message);
    error.stack = result.stack;
    throw error;
  } else
    return result.response;
};

async function getPopupPage(tab) {
  return await callTab(tab, "popupPath", []);
}

let injectionPromise;

async function connectToPage() {
  cLog("connecting to contentScript");
  const tab = await getCurrentTab();
  if (!tab)
    return;

  try {
    await getPopupPage(tab);
  } catch {
    cLog("error while sending to contentScript, trying to inject script", browser.runtime.lastError);
    let contentScript;
    for (const contentScript_ of browser.runtime.getManifest().content_scripts) {
      const tabs = await browser.tabs.query({
        active: true,
        lastFocusedWindow: true,
        url: contentScript_.matches,
      });
      if (tabs.length) {
        cLog("found matching content script", tabs, contentScript_);
        contentScript = contentScript_;
        break;
      }
    }
    if (!contentScript) {
      cLog("No content script matches current tab", tab);
      return null;
    }
    if (!injectionPromise)
      injectionPromise = injectContentScript(tab, contentScript);
    await injectionPromise;
    injectionPromise = null;
    cLog("content script injected, retrying");
    await getPopupPage(tab);
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
      globalThis.postMessage(message);
      return await new Promise((resolve, reject) => {
        async function handleResponse(event) {
          cLog("received from pageScript", event);
          if (event.source !== window)
            return;
          if (event.data.type === "donate4.fun-response") {
            globalThis.removeEventListener("message", handleResponse);
            resolve(event.data.result);
          } else if (event.data.type === "donate4.fun-exception") {
            globalThis.removeEventListener("message", handleResponse);
            reject(event.data.error);
          }
        }
        globalThis.addEventListener("message", handleResponse);
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

function registerHandlers(handlers) {
  browser.runtime.onMessage.addListener((request, sender) => {
    if (request.type !== 'donate4fun-request')
      return false;
    const handler = handlers[request.command];
    if (!handler) {
      cError(`Unexpected command ${request.command}`);
      return false;
    } else {
      cLog("Received request", request);
      return handleMessage(handler, request.args);
    }
  });
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
    width: 420,  // must be greater than popup.html size + frame size
    height: 640,
  });
  cLog("opened popup", window);
}

async function waitElement(selector) {
  let timeout = 3000;
  const step = 100;
  do {
    const element = document.querySelector(selector);
    if (element)
      return element;
    if (timeout <= 0)
      throw new Error(`No element with selector ${selector}`);
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
      const ws = subscribe(`donation:${donation.id}`, { autoReconnect: false });
      ws.on("notification", async () => {
        await ws.close();
        resolve(donation);
      });
      await ws.ready(3000);
      const paymentRequest = response.payment_request;
      // Show payment dialog (or pay silently if budget allows)
      try {
        await pageScript.sendPayment(paymentRequest);
      } catch (err) {
        await ws.close();
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

function selectByPattern(inputElement, pattern) {
  const selection = window.getSelection();
  const textNode = inputElement.childNodes[0];
  let match;
  selection.removeAllRanges();
  while (match = pattern.exec(inputElement.textContent)) {
    cLog("Match", match, textNode);
    // Select customizable part of text
    const range = document.createRange();
    range.setStart(textNode, match.index);
    range.setEnd(textNode, pattern.lastIndex);
    selection.addRange(range);
  }
}

export {
  worker,
  registerHandlers,
  browser,
  connectToPage,
  getCurrentTab,
  sleep,
  isTest,
  pageScript,
  injectContentScript,
  createPopup,
  waitElement,
  getStatic,
  donate,
  injectPageScript,
  selectByPattern,
};
