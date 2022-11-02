<script>
  import { get } from "svelte/store";
  import { useNavigate } from "svelte-navigator";
  import Button from "$lib/Button.svelte";
  import NeedHelp from "$lib/NeedHelp.svelte";
  import { webOrigin } from "$lib/utils.js";
  import { me } from "$lib/session.js";
  import cLog from "$lib/log.js";

  export let amount;
  export let rejected;
  export let historySource;
  const navigate = useNavigate();

  function onClose() {
    const state = historySource.history.state;
    cLog("state", state);
    if (state)
      navigate(-1);
    else
      window.close();
  }
</script>

<section class="popup flex-column">
  <Button
    on:click={onClose}
    --width=90px
    --padding="6.5px 26px"
    --font-size=16px
    --font-weight=500
    class=grey
  >Close</Button>
  <div class="content">
    {#if rejected === 'true'}
      <p class="message">You've rejected payment and you haven't enough sats on your Donate4.Fun balance. You may either</p>
      <Button
        --height=72px
        class=light
        target=_blank
        link="https://github.com/Donate4Fun/donate4fun/blob/master/docs/HELP.md#what-wallet-should-i-use"
      >Fulfill your wallet. How?</Button>
    {:else}
      <p class="message">You don't have enought sats and WebLN-enabled wallet is not available. You may either</p>
      <Button
        --height=72px
        class=light
        target=_blank
        link="{$webOrigin}/install-webln-wallet"
      >Get a WebLN-enabled wallet</Button>
    {/if}
    <p class="or">OR</p>
    {#await $me then me}
      <Button
        --height=72px
        target=_blank
        link="{$webOrigin}/fulfill/{me.donator.id}?amount={amount - (me.donator.balance || 0) + 1000}"
        class=white
        style="
          grid-row: fulfill;
        "
      >Fulfill your balance</Button>
    {:catch err}
      <p>Failed to load session {err}</p>
    {/await}
    <NeedHelp />
  </div>
</section>

<style>
section {
  visibility: visible;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(14.5px);
  gap: 77px;
  padding: 28px;
}
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}
.message {
  font-size: 20px;
  line-height: 26px;
  text-align: center;
}
.or {
  font-size: 16px;
  margin: -15px;
}
</style>
