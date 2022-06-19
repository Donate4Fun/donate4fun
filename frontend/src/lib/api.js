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
  }
};

export default api;
