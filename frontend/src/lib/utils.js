function copy(content) {
  navigator.clipboard.writeText(content);
  console.log("Copied to clipboard", content);
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
};
