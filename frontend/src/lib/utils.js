import { writable, get } from 'svelte/store';
import Analytics from 'analytics';
import googleAnalytics from '@analytics/google-analytics';
import plausiblePlugin from "analytics-plugin-plausible";
import { writable as writableStorage } from "svelte-local-storage-store";

export const webOrigin = writable(globalThis.location.origin);
export const isExtension = !globalThis.location.origin.startsWith('http');

export function resolve(path) {
  const origin = get(webOrigin);
  if (origin === location.origin)
    return path;
  else
    return origin + path;
}

export function copy(content) {
  if (window.isSecureContext) {
    navigator.clipboard.writeText(content);
    console.log("Copied to clipboard", content);
  } else {
    console.error("Could not use clipboard in insecure context");
  }
}

export function partial(func, ...args) {
  return () => {
    func(...args);
  }
}

export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function youtube_channel_url(channel_id) {
  return `https://youtube.com/channel/${channel_id}`;
}

export function youtube_video_url(video_id) {
  return `https://youtube.com/watch?v=${video_id}`;
}

export function youtube_studio_url(channel_id) {
  return `https://studio.youtube.com/channel/${channel_id}/editing/details`;
}

export function isWeblnPresent() {
  return !!window.webln;
}

export function isExtensionPresent() {
  return !!window.donate4fun || !!window.chrome;
}

export function toText(amount) {
  return amount >= 1000 ? `${amount / 1000} K` : amount;
}

export const trackingEnabled = writableStorage('track', null);

export const analytics = Analytics({
  app: "donate4fun",
  plugins: [
    plausiblePlugin({
      apiHost: "/proxy/event",
      trackLocalhost: true,
      enabled: !!get(trackingEnabled),
    }),
    googleAnalytics({
      measurementIds: ['G-K9B229WW3F'],
      enabled: !!get(trackingEnabled),
    }),
  ],
});

export function acceptTracking() {
  trackingEnabled.set(true);
  analytics.plugins.enable(['plausible-analytics', 'google-analytics']);
}

export function declineTracking() {
  trackingEnabled.set(false);
}
