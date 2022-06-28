<script>
  import {link} from "svelte-navigator";

  export let thumbnail_url;
  export let title;
  export let channel_id;
  export let id;

  let channel_url = `https://youtube.com/channel/${channel_id}`;
</script>

<span {...$$restProps}>
  <a href="/youtube-channel/{id}" use:link>
    {title}
  </a>
</span>

<style>
div a {
  display: flex;
  align-items: center;
}
</style>
