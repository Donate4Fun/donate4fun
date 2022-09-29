import { readable, get } from "svelte/store";
import api from "$lib/api.js";
import { storage } from "$lib/storage.js";

let loadPromise = null;

const obj = {
  loaded: null,
  load: null,
};

async function fetchMe() {
  const resp = await api.get("donator/me");
  console.log("Loaded user", resp);
  return resp;
}

function loadFrom(resp, set) {
  storage.me = resp;
  obj.donator = resp.donator;
  obj.youtube_channels = resp.youtube_channels;
  const pubkey = obj.donator.lnauth_pubkey;
  if (pubkey) {
    obj.shortkey = `@${pubkey.slice(0, 4)}…${pubkey.slice(-4)}`;
    obj.connected = true;
  } else {
    obj.connected = false;
  }

  obj.load = async () => {
    obj.loaded = new Promise(async (resolve) => {
      loadFrom(await fetchMe(), set);
      resolve();
    });
    set(obj);
    await obj.loaded;
  };
  set(obj);
}

export const me = readable(obj, function start(set) {
  obj.loaded = new Promise(async (resolve) => {
    if (!storage.me) {
      loadFrom(await fetchMe(), set);
    } else {
      loadFrom(storage.me, set);
    }
    resolve();
  });
  set(obj);
  return function stop() {};
});
