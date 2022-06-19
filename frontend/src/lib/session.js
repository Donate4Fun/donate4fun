import { writable, get } from "svelte/store";
import api from "../lib/api.js";


const { subscribe, update, set } = writable({})

export const me = {
  subscribe,

  init: async () => {
    const curr = get(me);
    if (!('donator' in curr)) { 
      const resp = await api.get("donator/me");
      console.log("Loaded user", resp);
      set(resp);
    }
  }
}
