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

export const analytics = Analytics({
  app: "donate4fun",
  plugins: [
    plausiblePlugin({
      apiHost: "/proxy/event",
      trackLocalhost: true,
    }),
    ...websiteOnlyPlugins,
  ],
});

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