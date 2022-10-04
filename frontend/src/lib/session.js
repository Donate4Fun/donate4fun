import { readable, writable, get } from "svelte/store";
import { api, apiOrigin } from "$lib/api.js";
import { storage } from "$lib/storage.js";
import jwt_decode from "jwt-decode";
import Cookies from "js-cookie";

export const cookies = writable();

const obj = {
  loaded: null,
  load: null,
  reset: null,
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
  obj.reset = async () => {
    Cookies.remove("session");
    await obj.load();
  };

  set(obj);
}

async function isValid() {
  if (!storage.me)
    return false;
  let sessionCookie;
  if (get(cookies)) {
    const cookie = await get(cookies).get({name: "session", url: get(apiOrigin)});
    if (!cookie)
      return false;
    sessionCookie = cookie.value;
  } else {
    sessionCookie = Cookies.get('session');
    if (!sessionCookie)
      return false;
  }
  const decoded = jwt_decode(sessionCookie);
  if (!decoded)
    return false;
  return decoded.donator === storage.me.donator.id;
}

export const me = readable(obj, function start(set) {
  obj.loaded = new Promise(async (resolve) => {
    if (!await isValid()) {
      console.log("stored session is invalid or missing, reloading");
      loadFrom(await fetchMe(), set);
    } else {
      loadFrom(storage.me, set);
    }
    resolve();
  });
  set(obj);
  return function stop() {};
});
