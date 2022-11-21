import axios from "axios";
import WebSocket from "async-ws";
import { notify } from "$lib/notifications.js";
import { writable, get as store_get } from 'svelte/store';
import { sleep } from "$lib/utils.js";
import { analytics } from "$lib/analytics.js";

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
    console.log(`received response for ${response.request.responseURL}`, response);
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

export async function get(path) {
  try {
    return handle_response(await axios.get(fullpath(path)));
  } catch (error) {
    return handle_error(error);
  }
}

export const api = {
  get,
  post,
  subscribe,
  errorToText,
};

export default api;
