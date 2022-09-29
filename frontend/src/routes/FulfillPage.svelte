<script>
  import { navigate, useLocation } from "svelte-navigator";

  import api from "$lib/api.js";
  import {me} from "$lib/session.js";
  import Donate from '$lib/Donate.svelte';
  import Donator from '$lib/Donator.svelte';
  import Page from "$lib/Page.svelte";
  import Section from "$lib/Section.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Loading from "$lib/Loading.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import {resolve} from "$lib/utils.js";

  export let donator_id;

  let donator;
  let amount = 100_000; // sats
  let spin = false;

  const amountMin = 10;
  const amountMax = 1000000;
  const location = useLocation();

  $: amountError = (() => {
    if (amount < amountMin)
      return `minimum: ${amountMin} sats`;
    else if (amount > amountMax)
      return `maximum: ${amountMax} sats`;
    else
      return null;
  })();

  async function load() {
    await $me.loaded;
    donator = await api.get(`donator/${donator_id}`);
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("amount"))
      amount = parseInt(urlParams.get("amount"));
  }

  async function donate(e) {
    spin = true;
    const response = await api.post('donate', {
        amount: amount,
        receiver_id: donator.id,
    });
    navigate(`/donation/${response.donation.id}`, {state: response});
    spin = false;
  }

  const loadPromise = load();
</script>

<svelte:head>
  {#await loadPromise then}
  <title>[Donate4Fun] Fulfill balance for {donator.name}</title>
  {/await}
</svelte:head>

<Page>
  <Section>
    {#await loadPromise}
    <Loading />
    {:then}
    <main>
      {#if $me.donator.id === donator_id}
        <h1 class="text-align-center">Fulfill your wallet</h1>
      {:else}
        <h1 class="text-align-center">Fulfill wallet for</h1>
      {/if}
      <Donator user={donator} />
      <div>
        <span>Amount:</span>
        <div class="amount"><Input type=number placeholder="Enter amount" bind:value={amount} min={amountMin} max={amountMax} bind:error={amountError} suffix=sats /></div><FiatAmount bind:amount={amount} class="fiat-amount" />
      </div>
      {#if $me.connected}
        <Button on:click={donate} disabled={amountError} --padding="10px 41px">
          <span>Fulfill</span>
        </Button>
      {:else}
        <Button link={resolve('/login') + '?return=' + $location.pathname} disabled={amountError} --padding="10px 41px">
          <span>Connect Wallet</span>
        </Button>
      {/if}
    </main>
    {/await}
  </Section>
</Page>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 46px 40px 46px;
  width: 640px;
  box-sizing: border-box;
}
main > h1 {
  margin-top: 0;
  margin-bottom: 24px;
}
main > div {
  display: flex;
  align-items: center;
  margin-top: 32px;
  margin-bottom: 36px;
  font-size: 18px;
}
.amount {
  width: 250px;
  margin-left: 16px;
  margin-right: 20px;
}
main :global(button) {
  width: 204px;
}
</style>
