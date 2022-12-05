<script>
  import { link } from "svelte-navigator";
  import { youtube_video_url } from "$lib/utils.js";

  export let video;
  export let linkto = 'external';
  export let target = '';
</script>

<div>
  <img src={video.youtube_channel.thumbnail_url} alt="youtube video logo">
  <span>
    {#if linkto === 'external'}
      <a target=_blank href={youtube_video_url(video.video_id)}>{video.title}</a>
    {:else if linkto === 'channel'}
      <a target={target} href="/youtube/{video.youtube_channel.id}" use:link>{video.title}</a>
    {/if}
  </span>
</div>

<style>
div {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
  min-width: 0;
}
img {
  width: 2em;
  border-radius: 50%;
}
span {
  text-overflow: ellipsis;
  min-width: 0;
  overflow: hidden;
  display: block;
  white-space: nowrap;
}
</style>
