import {
  registerHandlers,
  browser,
  getCurrentTab,
  injectContentScript,
  createPopup,
} from "./common.js";

async function handleFetch(method, path, data) {
  let response;
  const apiHost = await getConfig('apiHost');
  const url = `https://${apiHost}/api/v1/${path}`;
  if (method === "get") {
    response = await fetch(url, {
      headers: {
        'Accept': 'application/json'
      }
    });
  } else if (method === "post") {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  } else {
    throw new Error(`Unexpected method ${method}`);
  }
  if (response.status !== 200)
    throw response;
  else
    return await response.json();
}

const options = {
  checkInterval: {
    type: "number",
    default: 111,
    description: "Check interval when waiting for YouTube loading",
    dev: true,
    suffix: "ms",
  },
  apiHost: {
    type: "text",
    default: "donate4.fun",
    description: "API host",
    dev: true,
  },
  defaultComment_en: {
    type: "text",
    default: 'Nice video! I’ve donated you some 🪙₿, you can take it on "donate 4 fun" 🤑',
    description: "Default comment",
  },
  defaultComment_ru: {
    type: "text",
    default: 'Классное видео! Я задонатил тебе 🪙₿ на "donate 4 fun", загугли чтобы забрать 🤑',
    description: "Default comment (RU)",
  },
  amount: {
    type: "number",
    default: 100,
    description: "Donation amount",
    suffix: "sats",
  },
  enableComment: {
    type: "checkbox",
    default: true,
    description: "Enable auto-comment",
  },
  enableDevCommands: {
    type: "checkbox",
    default: false,
    description: "Enable development menu items in popup",
    dev: true,
  },
};

async function loadOptions() {
  const result = [];
  const values = await browser.storage.sync.get(getDefaults());
  for (const [key, value] of Object.entries(options)) {
    const item = {name: key, value: values[key]};
    Object.assign(item, value);
    item.dev = !!item.dev;
    result.push(item);
  }
  return result;
}

async function getConfig(name) {
  return await new Promise((resolve, reject) => {
    chrome.storage.sync.get(getDefaults(), items => {
      const value = items[name];
      if (value === undefined) {
        cLog(`No saved or default value for ${name} config key`);
        reject();
      } else {
        //console.log("sync.get", name, value);  // trace
        resolve(value);
      }
    });
  });
}

async function saveOptions(values) {
  await chrome.storage.sync.set(values);
}

async function setConfig(key, value) {
  return await new Promise((resolve, reject) => {
    const keys = {[key]: value};
    // console.log("sync.set", keys);  // trace
    chrome.storage.sync.set(keys, resolve);
  });
}

function getDefaults() {
  const defaults = {};
  for (const key in options)
    defaults[key] = options[key].default;
  return defaults;
}

async function resetConfig() {
  await chrome.storage.sync.set(getDefaults());
}

registerHandlers({
  fetch: handleFetch,
  loadOptions,
  saveOptions,
  getConfig,
  setConfig,
  resetConfig,
  injectContentScript,
  createPopup,
});

