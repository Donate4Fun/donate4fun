import { writable, get } from "svelte/store";
import api from "../lib/api.js";


const { subscribe, update, set } = writable({})

async function init() {
  const curr = get(me);
  if (!('donator' in curr)) { 
    await load();
  }
}

async function load() {
  if (window.webln)
    console.log("webln detected");
  const resp = await api.get("donator/me");
  console.log("Loaded user", resp);
  set(resp);
}


export const me = {
  subscribe,
  init: init,
  load: load
}
