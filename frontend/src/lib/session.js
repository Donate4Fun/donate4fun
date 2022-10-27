import { readable, writable, get } from "svelte/store";
import { asyncable } from 'svelte-asyncable';
import jwt_decode from "jwt-decode";
import Cookies from "js-cookie";

import { get as apiGet, apiOrigin, subscribe } from "$lib/api.js";
import { storage } from "$lib/storage.js";
import { cLog } from "$lib/log.js";
import { analytics } from "$lib/analytics.js";
import { isInsideExtension } from "$lib/utils.js";

// Store for browser.cookies
export const cookies = writable();
const cookieName = 'session';
let donatorWs;
let donatorWsId;

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
  analytics.identify(obj.donator.id, {
    pubkey: pubkey,
  });
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
  const browserCookies = get(cookies);
  if (browserCookies) {
    // Convert url to domain because Firefox does not allow to get secure cookie for http://localhost
    // (but shows for https://localhost or "localhost" domain)
    const cookieList = await browserCookies.getAll({name: cookieName, domain: getCookieDomain()});
    if (!cookieList.length)
      return false;
    sessionCookie = cookieList[0].value;
    browserCookies.onChanged.removeListener(onCookieChanged);
    browserCookies.onChanged.addListener(onCookieChanged);
  } else {
    sessionCookie = Cookies.get(cookieName);
    if (!sessionCookie)
      return false;
  }
  const decoded = jwt_decode(sessionCookie);
  if (!decoded)
    return false;
  return (
    decoded.donator === me.donator.id
    && decoded.lnauth_pubkey === me.donator.lnauth_pubkey
    && decoded.balance === me.donator.balance
  );
}

async function onCookieChanged(changeInfo) {
  cLog("onCookieChanged", changeInfo);
  const cookie = changeInfo.cookie;
  const domain = getCookieDomain();
  const domainNoDot = domain.slice(1);
  if (cookie.name === cookieName && !changeInfo.removed && (cookie.domain === domain || cookie.domain === domainNoDot)) {
    if (!await isValid())
      await reloadMe();
  }
}

export const me = asyncable(async () => {
  cLog("loading me");
  let me_;
  if (await isValid()) {
    me_ = loadFrom({}, storage.me);
  } else {
    console.log("stored session is invalid or missing, reloading");
    me_ = loadFrom({}, await fetchMe());
  }
  await subscribeToDonator(me_.donator.id);
  return me_;
});

async function subscribeToDonator(donatorId) {
  if (isInsideExtension())
    // TODO: implemet VAPID subscriptions in extension
    return;
  if (donatorWsId !== donatorId) {
    if (donatorWs)
      await donatorWs.close();
    donatorWs = subscribe(`donator:${donatorId}`);
    donatorWs.on("notification", () => {
      reloadMe();
    });
    donatorWsId = donatorId;
  }
}

export async function reloadMe() {
  const oldMe = await me.get();
  const newMe = loadFrom({}, await fetchMe());
  if (JSON.stringify(oldMe) !== JSON.stringify(newMe)) {
    await me.set(newMe);
    await subscribeToDonator(newMe.donator.id);
  }
}

export async function resetMe() {
  Cookies.remove(cookieName, { path: "/", domain: getCookieDomain() });
  Cookies.remove(cookieName, { path: "/" });
  await reloadMe();
}
