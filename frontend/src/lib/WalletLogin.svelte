<script>
  import {me} from "$lib/session.js";
  import Button from "$lib/Button.svelte";
  import {resolve} from "$lib/utils.js";

  export let target = null;
</script>

{#await $me}
  <Button class="grey">...</Button>
{:then me}
  <Button class="white" link={resolve('/login')} target={target} --padding="0" --height="40px" --width="160px" --border-width="1px">
    {#if me.connected}
      <div class="inner">
        <p class="connected">Wallet connected <img src="/static/checkbox.svg" alt="checkbox"></p>
        <p class="pubkey ellipsis">{me.shortkey}</p>
      </div>
    {:else}
      Connect Wallet
    {/if}
  </Button>
{:catch err}
  <p>Catch {err}</p>
{/await}
<style>
.inner {
  display: flex;
  flex-direction: column;
  color: var(--color);
}
.connected {
  display: flex;
  gap: 6px;
  align-items: center;

  font-weight: 500;
  font-size: 11px;
  line-height: 16px;
  letter-spacing: 0.01em;
}
.pubkey {
  font-weight: 700;
  font-size: 11px;
  line-height: 16px;
  text-align: left;
}
</style>
