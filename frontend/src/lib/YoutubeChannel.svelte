<script>
  import { link } from "svelte-navigator";

  export let thumbnail_url;
  export let title;
  export let channel_id;
  export let id;
  export let linkto = 'external';
</script>

<span {...$$restProps}>
  {#if linkto === 'external'}
  <a href="https://youtube.com/channel/{channel_id}" target="_blank">{title}</a>
  {:else if linkto === 'withdraw'}
  <a href="/youtube/{id}" use:link>{title}</a>
  {:else if linkto === 'donate'}
  <a href="/donate/{id}" use:link>{title}</a>
  {:else}
    Invalid linkto:
  {/if}
</span>
