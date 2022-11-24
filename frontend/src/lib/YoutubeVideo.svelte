<script>
  import { youtube_video_url } from "$lib/utils.js";
  export let video;
</script>

<div>
  <img src={video.youtube_channel.thumbnail_url} alt="youtube video logo">
  <span><a target=_blank href={youtube_video_url(video.video_id)}>{video.title}</a></span>
</div>

<style>
div {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
  width: 100%;
}
img {
  width: 2em;
  border-radius: 50%;
}
span {
  text-overflow: ellipsis;
  overflow: hidden;
  display: block;
  white-space: nowrap;
}
</style>
