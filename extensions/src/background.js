import {
  registerHandlers,
  browser,
  getCurrentTab,
  injectContentScript,
  createPopup,
} from "./common.js";
import cLog from "./log.js";

async function handleFetch(method, path, data) {
  let response;
  const apiHost = await getConfig('apiHost');
  const url = `${apiHost}/api/v1/${path}`;
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
  if (response.status !== 200) {
    const body = await response.text();
    console.error("Server error", body);
    throw new Error(`Server returned error: ${response.statusText} [${response.status}] ${body}`);
  } else
    return await response.json();
}

const Options = {
  amount: {
    type: "number",
    default: 100,
    description: "Donation amount",
    suffix: "sats",
  },
  enableComment: {
    type: "checkbox",
    default: true,
    description: "Enable 'Post a comment' popup",
  },
  defaultComment: {
    type: "text",
    default: '<WRITE YOUR COMMENT> I’ve donated you some 🪙₿, you can take it on "donate 4 fun" 🤑',
    description: "Default comment",
  },
  otherCommentLanguages: {
    type: "extendable",
    name: "Default comments by language",
    prefix: "defaultComment_",
    options: {
      defaultComment_ru: {
        type: "text",
        default: '<НАПИШИ СВОЙ КОММЕНТ> Я задонатил тебе 🪙₿ на "donate 4 fun", загугли чтобы забрать 🤑',
        description: "RU",
      },
    },
  },
  enableBoltButton: {
    type: "checkbox",
    default: true,
    description: "Enable bolt button on YouTube",
  },
  dev: {
    type: "section",
    name: "Developer options",
    options: {
      enableDevCommands: {
        type: "checkbox",
        default: false,
        description: "Enable development menu items in popup",
      },
      checkInterval: {
        type: "number",
        default: 111,
        description: "Check interval when waiting for YouTube loading",
        suffix: "ms",
      },
      apiHost: {
        type: "text",
        default: "https://donate4.fun",
        description: "API host",
      },
    },
  },
};

function assignOptionValues(options, values) {
  for (const [key, option] of Object.entries(options))
    if (option.type === 'section')
      assignOptionValues(option.options, values);
    else if (option.type === 'extendable') {
      assignOptionValues(option.options, values);
      for (const [storedKey, storedValue] of Object.entries(values)) {
        if (!(storedKey in option.options) && storedKey.startsWith(option.prefix))
          option.options[storedKey] = {
            type: "text",
            description: storedKey.substring(option.prefix.length).toUpperCase(),
            value: storedValue,
          };
      }
    } else
      option.value = Object.hasOwn(values, key) ? values[key] : option.default;
}

async function loadOptions() {
  const values = await browser.storage.sync.get();
  console.log("config values", values);
  const options = JSON.parse(JSON.stringify(Options));
  assignOptionValues(options, values);
  return options;
}

async function getConfig(name) {
  return await new Promise((resolve, reject) => {
    chrome.storage.sync.get(getDefaults(), items => {
      const value = items[name];
      if (value === undefined) {
        reject(new Error(`No saved or default value for ${name} config key`));
      } else {
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
    chrome.storage.sync.set(keys, resolve);
  });
}

function getDefaults() {
  const defaults = {};
  for (const [key, option] of Object.entries(Options))
    if (option.type === 'section')
      for (const [sectionKey, sectionOption] of Object.entries(option.options))
        defaults[sectionKey] = sectionOption.default;
    else
      defaults[key] = option.default;
  return defaults;
}

async function resetConfig() {
  await chrome.storage.sync.set(getDefaults());
}

browser.runtime.onInstalled.addListener(async (details) => {
  cLog("onInstalled", details);
  for (const contentScript of browser.runtime.getManifest().content_scripts)
    for (const tab of await browser.tabs.query({url: contentScript.matches}))
      try {
        await injectContentScript(tab, contentScript);
      } catch (err) {
        // This error happens on firefox for some reasone, We can ignore it because Firefox
        // injects content scripts on install automatically
        if (err.message !== 'An unexpected error occurred')
          console.error("Failed to inject content script", err, tab, contentScript);
      }
});

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
