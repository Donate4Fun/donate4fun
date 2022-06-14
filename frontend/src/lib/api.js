import axios from "axios";

class ApiError extends Error {
  constructor(message) {
    super(message);
    this.name = "ApiError";
  }
}

function handle_response(response) {
  if (response.status === 200) {
    return response.data;
  } else {
    console.log("API error", response);
    throw new ApiError(response.data);
  }
}

const api = {
  post: async (path, body) => {
    const resp = await axios.post(path, body);
    return handle_response(resp);
  },

  get: async (path) => {
    return handle_response(await axios.get(path));
  }
};

export default api;
