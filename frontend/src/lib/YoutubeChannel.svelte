<script>
  import { link } from "svelte-navigator";
  import { youtube_channel_url } from "$lib/utils.js";

  export let channel;
  export let linkto = 'external';
  export let logo = false;
</script>

<span {...$$restProps}>
  {#if logo}
    <img src={channel.thumbnail_url} alt="youtube channel logo">
  {/if}
  {#if linkto === 'external'}
    <a href={youtube_channel_url(channel.channel_id)} target="_blank">{channel.title}</a>
  {:else if linkto === 'withdraw'}
    <a href="/youtube/{channel.id}" use:link>{channel.title}</a>
  {:else if linkto === 'donate'}
    <a href="/donate/{channel.id}" use:link>{channel.title}</a>
  {:else}
    Invalid linkto:
  {/if}
</span>

<style>
span {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
}
img {
  width: 2em;
  border-radius: 50%;
}
</style>
