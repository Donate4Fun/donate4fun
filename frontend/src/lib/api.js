import axios from "axios";
import WebSocket from "async-ws";
import { notify } from "$lib/notifications.js";
import { writable, get as store_get } from 'svelte/store';
import { sleep } from "$lib/utils.js";

const apiOrigin = writable(window.location.origin);

class ApiError extends Error {
  constructor(response) {
    super(response.data.error);
    this.response = response;
    this.name = "ApiError";
  }
}

class ApiClientError extends Error {
}

function handle_response(response) {
  if (response.status === 200) {
    console.log(`received response for ${response.request.responseURL}`, response);
    return response.data;
  } else {
    console.error(`Server error in ${response.request?.responseURL}`, response);
    let message = response.data;
    if (typeof message !== "string")
      message = message.message || message.error || message.detail[0]?.msg || JSON.stringify(message);
    notify("Server Error", message, "error");
    throw new ApiError(response);
  }
}

function handle_error(error) {
  if (error.response && error.response !== error.request) {
    return handle_response(error.response);
  } else {
    console.error('HTTP error', error);
    notify("HTTP Error", error, "error");
    throw new ApiClientError(error);
  }
}

function fullpath(path) {
  return store_get(apiOrigin) + `/api/v1/${path}`;
}

function subscribe(topic) {
  const origin = store_get(apiOrigin).replace('http', 'ws');
  const wsUri = `${origin}/api/v1/subscribe/${topic}`;
  const ws = new WebSocket(wsUri);
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

async function post(path, body) {
  try {
    const resp = await axios.post(fullpath(path), body);
    return handle_response(resp);
  } catch (error) {
    return handle_error(error);
  }
}

async function get(path) {
  try {
    return handle_response(await axios.get(fullpath(path)));
  } catch (error) {
    return handle_error(error);
  }
}

globalThis.onError = function(message, source, lineno, colno, error) {
  console.log("onerror");
  notify("Error", message, "error");
}

export {
  get,
  post,
  subscribe,
  apiOrigin,
};
export default {
  get,
  post,
  subscribe,
};
