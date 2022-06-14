<script>
  import axios from 'axios';
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import QRCode from "../lib/QRCode.svelte";

  export let donation;
  export let payment_request;

	const dispatch = createEventDispatcher();

  onMount(() => {
    const loc = window.location;
    let scheme;
    if (loc.protocol === "https:") {
        scheme = "wss:";
    } else {
        scheme = "ws:";
    }
    const ws_uri = `${scheme}//${loc.host}/api/v1/donation/subscribe/${donation.id}`;
    const socket = new WebSocket(ws_uri);
    socket.onopen = (event) => {
      console.log("It's open");
    }
    socket.onmessage = (event) => {
      console.log("message", event);
      const data = JSON.parse(event.data)
      if (data.status === 'success') {
        if (data.state === 'SETTLED') {
          dispatch('paid', data.donation)
          return;
        }
      }
      console.error("unexpected invoice state", data);
    }
  })
</script>
<section>
  <h1>Lightning invoice</h1>
  <a href="lightning:{payment_request}"><QRCode value={payment_request} /></a>
  <div class="suggestion">Pay with a Wallet like
    <a href="https://muun.com" target="_blank">Muun</a>, 
    <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
    <a href="https://breez.technology" target="_blank">Breez</a> or 
    <a href="https://bluewallet.io" target="_blank">BlueWallet</a>
  </div>
  <a href="lightning:{payment_request}"><Button>Open in Wallet</Button></a>
  <Button on:click={navigator.clipboard.writeText(payment_request)}>Copy to clipboard</Button>
  <Button on:click={dispatch("cancel")}>Cancel</Button>
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
