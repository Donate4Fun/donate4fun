<script>
  import {createEventDispatcher, onMount, onDestroy} from 'svelte';
  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import QRCode from "$lib/QRCode.svelte";
  import Loading from "$lib/Loading.svelte";
  import Lnurl from "$lib/Lnurl.svelte";
  import Amount from "$lib/Amount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Donator from "$lib/Donator.svelte";
  import NeedHelp from "$lib/NeedHelp.svelte";
  import { partial, sendPayment } from "$lib/utils.js";
  import api from "$lib/api.js";
  import { me } from "$lib/session.js";

  export let donation;
  export let paymentRequest;

  let showQR = false;
  let ws;
  onDestroy(async () => {
    await ws?.close();
  });

	const dispatch = createEventDispatcher();

  async function subscribe() {
    ws = api.subscribe(`donation:${donation.id}`, { autoReconnect: false });
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        await ws.close();
        const response = await api.get(`donation/${donation.id}`);
        dispatch('paid', response.donation);
      }
    });
    await ws.ready(3000);
  }

  async function payWithWebLN() {
    // Show payment dialog (or pay silently if budget allows)
    try {
      await sendPayment(paymentRequest);
      return true;
    } catch (err) {
      // If WebLN fails show QR code
      return false;
    }
  }
</script>

<main>
  {#await subscribe()}
    <Loading />
  {:then}
    {#await payWithWebLN()}
      Trying to pay using WebLN
    {:then waitWebLN}
      {#if waitWebLN}
        <Loading />
      {:else}
        <a href="lightning:{paymentRequest}"><QRCode value={paymentRequest} /></a>
        <div class="buttons">
          <Button link="lightning:{paymentRequest}" --width=100%>Open in Wallet</Button>
          <Lnurl lnurl={paymentRequest} --width=100% />
          <GrayButton on:click={() => dispatch("cancel")} --width=100%>Back</GrayButton>
          <div class="need-help"><NeedHelp /></div>
        </div>
      {/if}
    {/await}
  {/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 300px;
}
.need-help {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.buttons {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
</style>
