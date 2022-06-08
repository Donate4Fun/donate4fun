<script>
  import axios from 'axios';
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import QRCode from "../lib/QRCode.svelte";

  export let invoice;
  let spinCancel = false;

	const dispatch = createEventDispatcher();
  const cancel = async () => {
    console.log("invoice cancel");
    spinCancel = true;
    try {
      await axios.post(`/api/v1/invoice/cancel/${invoice.r_hash}`);
    } catch (err) {
      console.error("Can't cancel invoice, ignoring:", err);
    }
    spinCancel = false;
    dispatch("cancel");
  }

  onMount(() => {
    const loc = window.location;
    let scheme;
    if (loc.protocol === "https:") {
        scheme = "wss:";
    } else {
        scheme = "ws:";
    }
    const ws_uri = `${scheme}//${loc.host}/api/v1/invoice/subscribe/${invoice.r_hash}`;
    const socket = new WebSocket(ws_uri);
    socket.onopen = (event) => {
      console.log("It's open");
    }
    socket.onmessage = (event) => {
      console.log("message", event);
      const data = JSON.parse(event.data)
      if (data.status === 'success') {
        if (data.state === 'SETTLED') {
          dispatch('paid', {amount: data.amount})
          return;
        }
      }
      console.error("unexpected invoice state", data);
    }
  })
</script>
<section>
  <h1>Lightning invoice</h1>
  <a href="lightning:{invoice.payment_request}"><QRCode value={invoice.payment_request} /></a>
  <div class="suggestion">Pay with a Wallet like
    <a href="https://muun.com" target="_blank">Muun</a>, 
    <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
    <a href="https://breez.technology" target="_blank">Breez</a> or 
    <a href="https://bluewallet.io" target="_blank">BlueWallet</a>
  </div>
  <a href="lightning:{invoice.payment_request}"><Button>Open in Wallet</Button></a>
  <Button on:click={navigator.clipboard.writeText(invoice.payment_request)}>Copy to clipboard</Button>
  <Button on:click={cancel}>
    {#if spinCancel}
    <Spinner />
    {/if}
    Cancel
  </Button>
</section>

<style>
section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1em;
}
section > :global(*) {
  --margin: 5px;
}
.suggestion {
  font-size: 16px;
  max-width: 20em;
}
.suggestion a {
  font-weight: 700;
}
section :global(button) {
  width: 25em;
}
section div {
  text-align: center;
}
</style>
