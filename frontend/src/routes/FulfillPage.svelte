<script>
  import { onMount } from "svelte";
  import api from "$lib/api.js";
  import {me} from "$lib/session.js";
  import Donate from '$lib/Donate.svelte';
  import Donator from '$lib/Donator.svelte';
  import Section from "$lib/Section.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Loading from "$lib/Loading.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import {resolve} from "$lib/utils.js";
  import title from "$lib/title.js";
  import cLog from "$lib/log.js";

  export let donator_id;
  export let location;
  export let navigate;

  const amountMin = 10;
  const amountMax = 1000000;

  let amount = 100_000; // sats
  let amountError = null;
  $: {
    if (amount < amountMin)
      amountError = `minimum: ${amountMin} sats`;
    else if (amount > amountMax)
      amountError = `maximum: ${amountMax} sats`;
    else
      amountError = null;
  };
  onMount(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.has("amount"))
      amount = parseInt(urlParams.get("amount"));
  });

  async function load(me) {
    cLog("load");
    let donator;
    if (donator_id === 'me') {
      donator = me.donator;
      donator_id = donator.id;
    } else {
      donator = await api.get(`donator/${donator_id}`);
    }
    title.set(`Fulfill balance for ${donator.name}`);
    return donator;
  }

  async function donate(e) {
    const response = await api.post('donate', {
      amount: amount,
      receiver_id: donator_id,
    });
    navigate(`/donation/${response.donation.id}`, {state: response});
  }
</script>

<Section>
  {#await $me}
    <Loading />
  {:then me}
    <main>
      {#if me.donator.id === donator_id}
        <h1 class="text-align-center">Fulfill your balance</h1>
      {:else}
        <h1 class="text-align-center">Donate to </h1>
      {/if}
      {#await load(me) then donator}
        <Donator user={donator} />
      {/await}
      <div class="amount">
        <span>Amount:</span>
        <div class="input">
          <Input type=number placeholder="Enter amount" bind:value={amount} min={amountMin} max={amountMax} bind:error={amountError} suffix=sats />
        </div>
        <FiatAmount bind:amount={amount} class="fiat-amount" />
      </div>
      <div class="button">
        {#if me.connected}
          <Button on:click={donate} disabled={amountError}>
            {#if me.donator.id === donator_id}
              <span>Fulfill</span>
            {:else}
              <span>Donate</span>
            {/if}
          </Button>
        {:else}
          <Button link={resolve('/login') + '?return=' + location.pathname} disabled={amountError}>
            <span>Connect Wallet</span>
          </Button>
        {/if}
      </div>
    </main>
  {/await}
</Section>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 46px 40px 46px;
  width: 640px;
  box-sizing: border-box;
}
h1 {
  margin-top: 0;
  margin-bottom: 24px;
}
.amount {
  display: flex;
  align-items: center;
  margin-top: 32px;
  margin-bottom: 36px;
  font-size: 18px;
}
.amount > .input {
  width: 250px;
  margin-left: 16px;
  margin-right: 20px;
}
.button {
  width: 204px;
}
</style>
