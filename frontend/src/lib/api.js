import axios from "axios";
import WebSocket from "async-ws";
import { notify } from "$lib/notifications.js";
import { readable, writable, get as store_get } from 'svelte/store';
import { sleep } from "$lib/utils.js";
import { analytics } from "$lib/analytics.js";
import { cLog, cError } from "$lib/log.js";

export const apiOrigin = writable(window.location.origin);

export class ApiError extends Error {
  constructor(response) {
    super(response.data.error);
    this.response = response;
    this.name = "ApiError";
  }
}

export class ApiClientError extends Error {
}

export function errorToText(response) {
  let message = response.data;
  if (typeof message !== "string")
    message = message.message || message.error || message.detail[0]?.msg || JSON.stringify(message);
  return `${response.statusText}: ${message}`;
}

function handle_response(response) {
  if (response.status === 200) {
    cLog(`received response for ${response.request.responseURL}`, response);
    return response.data;
  } else {
    console.error(`Server error in ${response.request?.responseURL}`, response);
    throw new ApiError(response);
  }
}

function handle_error(error) {
  if (error.response && error.response !== error.request) {
    return handle_response(error.response);
  } else {
    console.error('HTTP error', error);
    throw new ApiClientError(error);
  }
}

function fullpath(path) {
  return store_get(apiOrigin) + `/api/v1/${path}`;
}

export function subscribe(topic, options) {
  const origin = store_get(apiOrigin).replace('http', 'ws');
  if (!origin)
    throw new Error("apiOrigin is not defined");
  const wsUri = `${origin}/api/v1/subscribe/${topic}`;
  const ws = new WebSocket(wsUri, options);
  const origReady = ws.ready.bind(ws);
  ws.ready = async (timeout) => {
    if (timeout) {
      await Promise.race([origReady(), sleep(timeout)]);
      if (!ws._ready) {
        await ws.close(1000);
        throw new Error("timeout while connecting websocket");
      }
    } else {
      await origReady();
    }
  };
  ws.on("message", (msg) => {
    const notification = JSON.parse(msg.data);
    ws.emit("notification", notification);
  });
  return ws;
};

export async function post(path, body) {
  analytics.track(`api-${path}`);
  try {
    const resp = await axios.post(fullpath(path), body);
    return handle_response(resp);
  } catch (error) {
    return handle_error(error);
  }
}

export async function get(path, config) {
  try {
    return handle_response(await axios.get(fullpath(path), config));
  } catch (error) {
    return handle_error(error);
  }
}

export function apiStore(getPath, topic) {
  return readable(null, set => {
    const ws = subscribe(topic);
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK')
        set(await get(getPath));
    });
    (async () => {
      try {
        await ws.ready();
        set(await get(getPath));
      } catch (err) {
        cError("apiStore error", err);
        if (err.target instanceof WebSocket && err.target === 'error')
          notify("Network error", `WebSocket error while fetching ${topic}`, "error");
      }
    })();
    return () => ws.close();
  });
}

export function apiListStore(listPath, itemGetter, topic) {
  let set_;
  let items = [];
  const store = readable(null, set => {
    const ws = subscribe(topic);
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        const item = await itemGetter(notification.id);
        items = [item, ...items];
        set(items);
      }
    });
    (async () => {
      await ws.ready();
      items = await get(listPath);
      set(items);
      set_ = set;
    })();
    return () => ws.close();
  });

  return {
    subscribe: store.subscribe,
    async loadMore() {
      // FIXME: it can return duplicates that already exist in items or return with gap
      // due to race conditions
      const newItems = await api.get(`${listPath}?offset=${items.length}`);
      items = [...items, ...newItems];
      set_(items);
    }
  };
}

export function socialDonationsStore(socialProvider, accountId) {
  return apiStore(
    `social/${socialProvider}/${accountId}/donations/by-donatee`,
    `social:${socialProvider}:${accountId}`,
  );
}

export const api = {
  get,
  post,
  subscribe,
  errorToText,
  apiStore,
  socialDonationsStore,
};

export default api;
