<script>
  import { link } from "svelte-navigator";
  import Thumbnail from "$lib/Thumbnail.svelte";
  import { youtube_channel_url } from "$lib/utils.js";

  export let channel;
  export let linkto = 'external';
  export let logo = false;
  export let target = '';
</script>

<span {...$$restProps}>
  {#if logo}
    <Thumbnail url={channel.thumbnail_url} />
  {/if}
  {#if linkto === 'external'}
    <a href={youtube_channel_url(channel.channel_id)} target="_blank">{channel.title}</a>
  {:else if linkto === 'withdraw'}
    <a href="/youtube/{channel.id}" target={target} use:link>{channel.title}</a>
  {:else if linkto === 'donate'}
    <a href="/donate/{channel.id}" target={target} use:link>{channel.title}</a>
  {:else}
    Invalid linkto:
  {/if}
</span>

<style>
span {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
  min-width: 0;
}
</style>
