import axios from "axios";
import {notify} from "../lib/notifications.js";

class ApiError extends Error {
  constructor(response) {
    super(response.data.error);
    this.response = response;
    this.name = "ApiError";
  }
}

function handle_response(response) {
  if (response.status === 200) {
    console.log(`received response for ${response.request.responseURL}`, response);
    return response.data;
  } else {
    console.error(`API error in ${response.request.responseURL}`, response);
    throw new ApiError(response);
  }
}

function fullpath(path) {
  return `/api/v1/${path}`
}

function createWebsocket(topic, on_message, on_close) {
  const loc = window.location;
  let scheme;
  if (loc.protocol === "https:") {
      scheme = "wss:";
  } else {
      scheme = "ws:";
  }
  const ws_uri = `${scheme}//${loc.host}/api/v1/subscribe/${topic}`;

  const socket = new WebSocket(ws_uri);
  socket.onmessage = (event) => {
    console.log(`[ws] Message from ${topic}`, event);
    try {
      const msg = JSON.parse(event.data)
      on_message(msg)
    } catch (err) {
      console.error(`unexpected websocket ${topic} notification`, err, event);
    }
  };
  socket.onerror = (event) => {
    console.log(`[ws] Error in ${topic}`, event);
  };
  socket.onclose = (event) => {
    console.log(`[ws] Closed ${topic}`, event);
    on_close();
  };
  console.log(`[ws] ${topic} opening`);
  return socket;
}

async function subscribe(topic, on_message) {
  let socket;
  let opened = true;
  function onClose() {
    if (opened) {
      socket = createWebsocket(topic, on_message, onClose);
      socket.onopen = _ => {
        console.log(`[ws] ${topic} opened`);
      };
    }
  }
  socket = createWebsocket(topic, on_message, onClose);
  await new Promise((resolve, reject) => {
    socket.onopen = _ => {
      console.log(`[ws] ${topic} opened`);
      resolve();
    };
  });
  return () => {
    opened = false;
    socket.close();
    console.log(`[ws] ${topic} unsubscribed`);
  };
}

const api = {
  post: async (path, body) => {
    try {
      const resp = await axios.post(fullpath(path), body);
      return handle_response(resp);
    } catch (error) {
      return handle_response(error.response);
    }
  },

  get: async (path) => {
    try {
      return handle_response(await axios.get(fullpath(path)));
    } catch (error) {
      return handle_response(error.response);
    }
  },

  subscribe: subscribe
};

window.onError = function(message, source, lineno, colno, error) {
  console.log("onerror");
  notify("Error", message, "error"); 
}

export default api;
