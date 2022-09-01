<script>
  import { navigate } from "svelte-navigator";

  import api from "../lib/api.js";
  import {me} from "../lib/session.js";
  import Donate from '../lib/Donate.svelte';
  import Donator from '../lib/Donator.svelte';
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Input from "../lib/Input.svelte";
  import FiatAmount from "../lib/FiatAmount.svelte";
  import Button from "../lib/Button.svelte";
  import Loading from "../lib/Loading.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";

  export let donator_id;

  let donator;

  let amount = 100;
  let spin = false;

  const amountMin = 10;
  const amountMax = 1000000;

  $: isValid = amount >= amountMin;
  $: amountError = (() => {
    if (amount < amountMin)
      return `minimum: ${amountMin} sats`;
    else if (amount > amountMax)
      return `maximum: ${amountMax} sats`;
    else
      return null;
  })();

  async function load() {
    await me.init();
    donator = await api.get(`donator/${donator_id}`);
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
  <title>Donate4Fun to {donator.name}</title>
  {/await}
</svelte:head>

<Page>
  <header>
    {#await loadPromise then}
      {#if $me.donator.id === donator_id}
      <h1>Fulfill your balance</h1>
      {:else}
      <h1>Donate to {donator.name}</h1>
      {/if}
    {/await}
  </header>
  <Section>
    {#await loadPromise}
    <Loading />
    {:then}
    <main>
      <h1>Donate to</h1>
      <Donator user={donator} />
      <div>
        <span class="i-want">Donate</span>
        <div class="amount"><Input type=number placeholder="Enter amount" bind:value={amount} min={amountMin} max={amountMax} bind:error={amountError} suffix=sats /></div><FiatAmount bind:amount={amount} class="fiat-amount" />
      </div>
      <Button on:click={donate} disabled={!isValid}>
        <span>Donate</span>
      </Button>
    </main>
    {/await}
  </Section>
</Page>

<style>
header {
  margin-bottom: 56px;
  font-size: 24px;
}
header > h1 {
  margin-bottom: 16px;
  font-size: 44px;
  font-weight: 900;
}
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
