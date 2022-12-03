import { readable, writable, get } from 'svelte/store';
import { custom_event, get_current_component } from 'svelte/internal'
import cLog from "$lib/log.js";

export const webOrigin = writable(globalThis.location.origin);
export const isExtension = !globalThis.location.origin.startsWith('http');

export function resolve(path) {
  const origin = get(webOrigin);
  if (origin === location.origin)
    return path;
  else
    return origin + path;
}

export function copy(content) {
  if (globalThis.isSecureContext) {
    navigator.clipboard.writeText(content);
    console.log("Copied to clipboard", content);
  } else {
    console.error("Could not use clipboard in insecure context");
  }
}

export function partial(func, ...args) {
  return () => {
    func(...args);
  }
}

export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function youtube_channel_url(channel_id) {
  return `https://youtube.com/channel/${channel_id}`;
}

export function youtube_video_url(video_id) {
  return `https://youtube.com/watch?v=${video_id}`;
}

export function youtube_studio_url(channel_id) {
  return `https://studio.youtube.com/channel/${channel_id}/editing/details`;
}

export function isWeblnPresent() {
  return !!globalThis.webln;
}

export function isInsideExtension() {
  return typeof globalThis.chrome?.extension === 'object';
}

export function isExtensionPresent() {
  return !!globalThis.donate4fun || isInsideExtension();
}

function makeStore(func) {
  return readable(func(), (set) => {
    function update() {
      set(func());
    }
    window.addEventListener("load", update);
    return () => {
      window.removeEventListener("load", update);
    };
  });
}

export const extensionPresent = makeStore(isExtensionPresent);
export const weblnPresent = makeStore(isWeblnPresent);

export function toText(amount) {
  return amount >= 1000 ? `${amount / 1000} K` : amount;
}

export async function sendPayment(request) {
  if (!window.webln)
    throw new Error("No webln found");
  if (!webln.enabled) {
    // Show connect dialog
    await webln.enable();
  }
  const result = await webln.sendPayment(request);
  cLog("webln.sendPayment result", result);
}

export function capitalize(s) {
  if (typeof s !== 'string')
    return '';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// This dispatcher returns promise
function createAwaitableDispatcher() {
  const component = get_current_component();

  return (type, detail) => {
    const callbacks = component.$$.callbacks[type];

    if (callbacks) {
      // TODO are there situations where events could be dispatched
      // in a server (non-DOM) environment?
      const arr = [];
      const hasCallbacks = !!callbacks.length;
      const event = custom_event(type, detail);
      callbacks.slice().forEach(fn => {
        const res = fn.call(component, event);
        if (res instanceof Promise) {
          arr.push(res);
        }
      });
      return Promise.all(arr).then(() => hasCallbacks);
    }
    return new Promise((resolve) => resolve(false));
  };
}

export function clickDispatcher() {
  const dispatch = createAwaitableDispatcher();
  return async function click(ev) {
    return await dispatch("click", ev);
  };
}
