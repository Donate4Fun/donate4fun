import { writable, get } from "svelte/store";
import api from "../lib/api.js";


const { subscribe, update, set } = writable({});

let loadPromise = null;

async function init() {
  if (loadPromise === null) {
    const curr = get(me);
    if (!('donator' in curr)) {
      loadPromise = load();
    }
  }
  await loadPromise;
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
