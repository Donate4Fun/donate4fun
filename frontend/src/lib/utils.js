import {useResolve} from "svelte-navigator";
import {writable, get} from 'svelte/store';

export const webOrigin = writable(window.location.origin);
export const isExtension = !window.location.origin.startsWith('http');

function resolve(path) {
  const origin = get(webOrigin);
  return `${origin}${path}`;
}

function copy(content) {
  if (window.isSecureContext) {
    navigator.clipboard.writeText(content);
    console.log("Copied to clipboard", content);
  } else {
    console.error("Could not use clipboard in insecure context");
  }
}

function partial(func, ...args) {
  return () => {
    func(...args);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function youtube_channel_url(channel_id) {
  return `https://youtube.com/channel/${channel_id}`;
}

function youtube_video_url(video_id) {
  return `https://youtube.com/watch?v=${video_id}`;
}

function youtube_studio_url(channel_id) {
  return `https://studio.youtube.com/channel/${channel_id}/editing/details`;
}

export {
  copy,
  partial,
  sleep,
  youtube_studio_url,
  youtube_video_url,
  youtube_channel_url,
  resolve,
};
