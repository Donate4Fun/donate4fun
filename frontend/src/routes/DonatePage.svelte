<script>
  import { navigate } from "svelte-navigator";

  import api from "$lib/api.js";
  import Donate from '$lib/Donate.svelte';
  import Section from "$lib/Section.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Loading from "$lib/Loading.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import title from "$lib/title.js";

  export let channel_id;

  let amount = 100;
  let spin = false;
  let youtube_channel;

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
    youtube_channel = await api.get(`youtube-channel/${channel_id}`);
    title.set(`Donate4Fun to ${youtube_channel.title}`);
  }

  async function donate(e) {
    spin = true;
    const response = await api.post('donate', {
        amount: amount,
        channel_id: youtube_channel.id,
    });
    navigate(`/donation/${response.donation.id}`, {state: response});
    spin = false;
  }
</script>

<Section>
  {#await load()}
    <Loading />
  {:then}
    <form on:submit|preventDefault={donate}>
      <h1>Donate to <YoutubeChannel channel={youtube_channel} /></h1>
      <ChannelLogo url={youtube_channel.thumbnail_url} />
      <div>
        <span class="i-want">Donate</span>
        <div class="amount">
          <Input type=number placeholder="Enter amount" bind:value={amount} min={amountMin} max={amountMax} bind:error={amountError} suffix=sats />
        </div>
        <FiatAmount bind:amount={amount} class="fiat-amount" />
      </div>
      <Button class="submit" type=submit disabled={!isValid}>
        {#if spin}
          <Spinner --size=20px --width=3px />
        {/if}
        <span>Donate</span>
      </Button>
    </form>
  {/await}
</Section>

<style>
header {
  margin-bottom: 56px;
  font-size: 24px;
  text-align: center;
}
header > h1 {
  margin-bottom: 16px;
  font-size: 44px;
  font-weight: 900;
}
form {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 72px;
  width: 640px;
  box-sizing: border-box;
}
form > h1 {
  margin-top: 0;
  margin-bottom: 24px;
  display: flex;
  gap: 0.5em;
}
form > div {
  display: flex;
  align-items: center;
  margin-top: 32px;
  margin-bottom: 36px;
  font-size: 18px;
  width: 100%;
}
.amount {
  width: 250px;
  margin-left: 16px;
  margin-right: 20px;
  flex-grow: 1;
}
form :global(button) {
  width: 204px;
}
</style>
