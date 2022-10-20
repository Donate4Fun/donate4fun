import { get } from "svelte/store";
import Analytics from 'analytics';
import googleAnalytics from '@analytics/google-analytics';
import plausiblePlugin from "analytics-plugin-plausible";
import { writable as writableStorage } from "svelte-local-storage-store";
import { isInsideExtension } from "$lib/utils.js";

export const trackingEnabled = writableStorage('track', null);

const websiteOnlyPlugins = isInsideExtension() ? [] : [googleAnalytics({
  measurementIds: ['G-K9B229WW3F'],
  enabled: !!get(trackingEnabled),
})];

export const analytics = Analytics({
  app: "donate4fun",
  plugins: [
    plausiblePlugin({
      apiHost: "/proxy/event",
      trackLocalhost: true,
      enabled: !!get(trackingEnabled),
    }),
    ...websiteOnlyPlugins,
  ],
});

export function acceptTracking() {
  trackingEnabled.set(true);
  analytics.plugins.enable(['plausible-analytics', 'google-analytics']);
}

export function declineTracking() {
  trackingEnabled.set(false);
}
