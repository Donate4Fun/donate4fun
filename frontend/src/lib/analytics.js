import { get } from "svelte/store";
import Analytics from 'analytics';
import googleAnalytics from '@donate4fun/google-analytics/src/browser.js';
import plausiblePlugin from "analytics-plugin-plausible";
import { writable as writableStorage } from "svelte-local-storage-store";
import { isInsideExtension } from "$lib/utils.js";

export const trackingEnabled = writableStorage('track', null);

const websiteOnlyPlugins = isInsideExtension() ? [] : [googleAnalytics({
  measurementIds: ['G-K9B229WW3F'],
})];
const plugins = import.meta.env.DEV ? [] : [
  plausiblePlugin({
    apiHost: "/proxy/event",
    trackLocalhost: true,
  }),
];

// Workaround for
// >> TypeError: 'addEventListener' called on an object that does not implement interface EventTarget.
// window object does not implement EventTarget inside content script context
// (it's used here https://github.com/DavidWells/analytics/blob/052bd9262f92758f024248b35dc044d7aca74d4a/packages/analytics-core/src/utils/handleNetworkEvents.js#L5)
const origAdd = window?.addEventListener;
if (window)
  window.addEventListener = () => {};
export const analytics = Analytics({
  app: "donate4fun",
  plugins: [
    ...plugins,
    ...websiteOnlyPlugins,
  ],
});
if (window)
  window.addEventListener = origAdd;

analytics.on("ready", () => {
  if (!isInsideExtension()) {
    window.gtag('consent', 'default', {
      'ad_storage': 'denied',
      'analytics_storage': 'denied',
    });
  }
  if (get(trackingEnabled))
    acceptTracking();
});

export function acceptTracking() {
  trackingEnabled.set(true);
  if (!isInsideExtension()) {
    globalThis.gtag('consent', 'update', {
      'analytics_storage': 'granted',
    });
  }
}

export function declineTracking() {
  trackingEnabled.set(false);
}
