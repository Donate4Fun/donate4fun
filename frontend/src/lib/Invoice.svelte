<script>
  import { createEventDispatcher } from 'svelte';
  import Button from "../lib/Button.svelte";
  import QRCode from "../lib/QRCode.svelte";

  export let invoice;

	const dispatch = createEventDispatcher();
  function cancel() {
    console.log("invoice cancel");
    dispatch("cancel");
  }
</script>
<section>
  <h1>Lightning invoice</h1>
  <a href="lightning:{invoice.payment_request}"><QRCode value={invoice.payment_request} /></a>
  <div>Pay with a Wallet like
    <a href="https://muun.com" target="_blank">Muun</a>, 
    <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
    <a href="https://breez.technology" target="_blank">Breez</a> or 
    <a href="https://bluewallet.io" target="_blank">BlueWallet</a>
  </div>
  <a href="lightning:{invoice.payment_request}"><Button>Open in Wallet</Button></a>
  <Button on:click={navigator.clipboard.writeText(invoice.payment_request)}>Copy to clipboard</Button>
  <Button on:click={cancel}>Cancel</Button>
</section>

<style>
section {
  display: flex;
  flex-direction: column;
  align-items: center;
}
section :global(button) {
  width: 15em;
}
section div {
  text-align: center;
}
</style>
