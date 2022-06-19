<script>
  import {link} from "svelte-navigator";

  export let thumbnail_url;
  export let title;
  export let channel_id;
  export let id;

  let channel_url = `https://youtube.com/channel/${channel_id}`;
</script>

<div>
  <a href="/youtube-channel/{id}" use:link>
    <img src={thumbnail_url} alt="youtube channel logo">
    {title}
  </a>
</div>

<style>
div a {
  display: flex;
  align-items: center;
}
div a img {
  width: 2em;
  height: 2em;
}
</style>
