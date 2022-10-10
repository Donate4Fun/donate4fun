import { readable, writable, get } from "svelte/store";
import { get as apiGet, apiOrigin } from "$lib/api.js";
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
  const resp = await apiGet("donator/me");
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
  return obj;
}

function getCookieDomain() {
  // Take first-level domain
  const hostname = new URL(get(apiOrigin)).hostname;
  return "." + hostname.split('.').slice(-2).join('.');
}

async function isValid() {
  const me = storage.me;
  if (!me)
    return false;
  let sessionCookie;
  if (get(cookies)) {
    // Convert url to domain because Firefox does not allow to get secure cookie for http://localhost
    // (but shows for https://localhost or "localhost" domain)
    const cookieList = await get(cookies).getAll({name: "session", domain: getCookieDomain()});
    if (!cookieList.length)
      return false;
    sessionCookie = cookieList[0].value;
  } else {
    sessionCookie = Cookies.get('session');
    if (!sessionCookie)
      return false;
  }
  const decoded = jwt_decode(sessionCookie);
  if (!decoded)
    return false;
  return decoded.donator === me.donator.id && decoded.lnauth_pubkey === me.donator.lnauth_pubkey;
}

export const me = readable(obj, function start(set) {
  obj.load = async () => {
    obj.loaded = new Promise(async (resolve) => {
      loadFrom(await fetchMe(), set);
      resolve();
    });
    set(obj);
    await obj.loaded;
  };
  obj.reset = async () => {
    Cookies.remove("session", { path: "/", domain: getCookieDomain() });
    Cookies.remove("session", { path: "/" });
    await obj.load();
  };

  obj.loaded = new Promise(async (resolve) => {
    if (!await isValid()) {
      console.log("stored session is invalid or missing, reloading");
      set(loadFrom(await fetchMe()));
    } else {
      set(loadFrom(storage.me));
    }
    resolve();
  });
  set(obj);
  return function stop() {};
});
