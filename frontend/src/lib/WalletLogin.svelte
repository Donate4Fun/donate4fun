<script>
  import { me } from "$lib/session.js";
  import Button from "$lib/Button.svelte";
  import WhiteButton from "$lib/WhiteButton.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import Amount from "$lib/Amount.svelte";
  import { resolve } from "$lib/utils.js";

  export let target = null;
</script>

{#await $me}
  <GrayButton disabled>...</GrayButton>
{:then me}
  <WhiteButton link={resolve('/signin')} target={target} --height="40px" --width="160px" --border-width="2px">
    {#if me.connected}
      <div class="inner">
        <p class="connected"><Amount amount={me.donator.balance} /></p>
      </div>
    {:else}
      Sign in
    {/if}
  </WhiteButton>
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
</style>
