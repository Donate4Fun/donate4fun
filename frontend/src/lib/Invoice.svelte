<script>
  import {createEventDispatcher, onMount, onDestroy} from 'svelte';
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Loading from "../lib/Loading.svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import { partial } from "../lib/utils.js";
  import api from "../lib/api.js";

  export let donation;
  export let payment_request;
  let unsubscribe = null;
  onDestroy(() => {
    if (unsubscribe !== null) {
      unsubscribe();
    }
  });

	const dispatch = createEventDispatcher();

  async function subscribe() {
    unsubscribe = await api.subscribe(`donation:${donation.id}`, async (notification) => {
      if (notification.status === 'OK') {
        unsubsribe();
        const response = await api.get(`donation/${donation.id}`);
        dispatch('paid', response.donation);
      }
    });
  }
</script>

<main>
  {#await subscribe()}
  <Loading />
  {:then}
  <h1>Donate <Amount amount={donation.amount} /> to <YoutubeChannel {...donation.youtube_channel} /></h1>
  <a href="lightning:{payment_request}"><QRCode value={payment_request} /></a>
  <div class="suggestion">Pay with a Wallet like
    <a href="https://getalby.com" target="_blank">Alby</a>, 
    <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
    <a href="https://sbw.app" target="_blank">SBW</a> or 
    <a href="https://blixtwallet.github.io" target="_blank">Blixt</a>
  </div>
  <a href="lightning:{payment_request}"><Button>Open in Wallet</Button></a>
  <Lnurl lnurl={payment_request} class="lnurl" />
  <Button on:click={partial(dispatch, "cancel")} class="grey">Back</Button>
  {/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 36px 119px 40px 119px;
  gap: 20px;
}
h1 {
  font-weight: 900;
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}
.suggestion {
  font-size: 16px;
  width: 402px;
  margin-top: 4px;
  margin-bottom: 8px;
}
.suggestion a {
  font-weight: 700;
}
main :global(button) {
  width: 402px;
  height: 44px;
  font-weight: 700;
}
main :global(.lnurl) {
  width: 402px;
}
main div {
  text-align: center;
}
</style>
