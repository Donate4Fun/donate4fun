<script>
  import { link } from "svelte-navigator";

  export let channel;
  export let linkto = 'external';
</script>

<span {...$$restProps}>
  {#if linkto === 'external'}
  <a href="https://youtube.com/channel/{channel.channel_id}" target="_blank">{channel.title}</a>
  {:else if linkto === 'withdraw'}
  <a href="/youtube/{channel.id}" use:link>{channel.title}</a>
  {:else if linkto === 'donate'}
  <a href="/donate/{channel.id}" use:link>{channel.title}</a>
  {:else}
    Invalid linkto:
  {/if}
</span>
