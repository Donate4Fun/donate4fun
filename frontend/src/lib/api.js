import axios from "axios";

class ApiError extends Error {
  constructor(message) {
    super(message);
    this.name = "ApiError";
  }
}

function handle_response(response) {
  if (response.status === 200) {
    console.log("received response", response);
    return response.data;
  } else {
    console.error("API error", response);
    throw new ApiError(response.data);
  }
}

function fullpath(path) {
  return `/api/v1/${path}`
}

const api = {
  post: async (path, body) => {
    const resp = await axios.post(fullpath(path), body);
    return handle_response(resp);
  },

  get: async (path) => {
    return handle_response(await axios.get(fullpath(path)));
  },

  subscribe: async (path, on_message) => {
    const loc = window.location;
    let scheme;
    if (loc.protocol === "https:") {
        scheme = "wss:";
    } else {
        scheme = "ws:";
    }
    const ws_uri = `${scheme}//${loc.host}/api/v1/${path}`;
    const socket = new WebSocket(ws_uri);
    socket.onmessage = (event) => {
      console.log(`Message from ${path}`, event);
      try {
        const msg = JSON.parse(event.data)
        on_message(msg)
      } catch (err) {
        console.error(`unexpected websocket ${path} notification`, err, event);
      }
    }
    await new Promise((resolve, reject) => {
      socket.onopen = _ => {
        console.log(`Websocket ${path} open`);
        resolve();
      };
    });
  }
};

export default api;
