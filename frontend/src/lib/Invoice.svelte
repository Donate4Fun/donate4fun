<script>
  import {createEventDispatcher, onMount, onDestroy} from 'svelte';
  import Button from "../lib/Button.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Loading from "../lib/Loading.svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Donator from "../lib/Donator.svelte";
  import NeedHelp from "$lib/NeedHelp.svelte";
  import { partial } from "../lib/utils.js";
  import api from "../lib/api.js";
  import { me } from "$lib/session.js";

  export let donation;
  export let payment_request;

  let ws;
  onDestroy(async () => {
    await ws?.close();
  });

	const dispatch = createEventDispatcher();

  async function subscribe() {
    ws = api.subscribe(`donation:${donation.id}`);
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        await ws.close();
        const response = await api.get(`donation/${donation.id}`);
        dispatch('paid', response.donation);
      }
    });
    await ws.ready();
  }
</script>

<main>
  {#await subscribe()}
    <Loading />
  {:then}
    {#if donation.youtube_channel}
      <h1>Donate <Amount amount={donation.amount} /> to</h1>
      <YoutubeChannel channel={donation.youtube_channel} />
    {:else if donation.receiver}
      {#await $me then me}
        {#if donation.receiver.id === me.donator.id}
          <h1>Fulfill <Amount amount={donation.amount} /> to your wallet</h1>
        {:else}
          <h1>Donate <Amount amount={donation.amount} /> to <Donator user={donation.receiver} /></h1>
        {/if}
      {/await}
    {/if}
    <a href="lightning:{payment_request}"><QRCode value={payment_request} /></a>
    <div class="buttons flex-column gap-20">
      <Button link="lightning:{payment_request}" --width=100%>Open in Wallet</Button>
      <Lnurl lnurl={payment_request} --width=100% />
      <Button on:click={partial(dispatch, "cancel")} class="grey" --width=100%>Back</Button>
      <div class="need-help"><NeedHelp /></div>
    </div>
  {/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 58px 16px 56px;
}
h1 {
  font-weight: 900;
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}
.need-help {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.buttons {
  width: 295px;
}
</style>
