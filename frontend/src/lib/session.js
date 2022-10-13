import { readable, writable, get } from "svelte/store";
import { asyncable } from 'svelte-asyncable';
import { get as apiGet, apiOrigin } from "$lib/api.js";
import { storage } from "$lib/storage.js";
import { cLog } from "$lib/log.js";
import jwt_decode from "jwt-decode";
import Cookies from "js-cookie";

export const cookies = writable();

async function fetchMe() {
  const resp = await apiGet("donator/me");
  console.log("Loaded user", resp);
  return resp;
}

function loadFrom(obj, resp) {
  storage.me = resp;
  obj.donator = resp.donator;
  obj.youtube_channels = resp.youtube_channels;
  const pubkey = resp.donator.lnauth_pubkey;
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

export const me = asyncable(async () => {
  cLog("loading me");
  if (await isValid()) {
    return loadFrom({}, storage.me);
  } else {
    console.log("stored session is invalid or missing, reloading");
    return loadFrom({}, await fetchMe());
  }
});

export async function reloadMe() {
  const oldMe = await me.get();
  const newMe = loadFrom({}, await fetchMe());
  if (JSON.stringify(oldMe) !== JSON.stringify(newMe))
    await me.set(newMe);
}

export async function resetMe() {
  Cookies.remove("session", { path: "/", domain: getCookieDomain() });
  Cookies.remove("session", { path: "/" });
  await reloadMe();
}
