<script>
  import {createEventDispatcher, onMount, onDestroy} from 'svelte';
  import Button from "../lib/Button.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Loading from "../lib/Loading.svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Donator from "../lib/Donator.svelte";
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
        unsubscribe();
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
    {#if donation.youtube_channel}
      <h1>Donate <Amount amount={donation.amount} /> to</h1>
      <YoutubeChannel channel={donation.youtube_channel} />
    {:else if donation.receiver}
      <h1>Fulfill <Amount amount={donation.amount} /> to your wallet</h1>
    {/if}
    <a href="lightning:{payment_request}"><QRCode value={payment_request} /></a>
    <div class="suggestion font-weight-700 text-align-center">
      <span>Pay with a Wallet like</span>
      <a href="https://getalby.com" target="_blank">Alby</a>,
      <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>,
      <a href="https://sbw.app" target="_blank">SBW</a> or
      <a href="https://blixtwallet.github.io" target="_blank">Blixt</a>
    </div>
    <div class="buttons flex-column gap-20">
      <Button link="lightning:{payment_request}" --width=100%>Open in Wallet</Button>
      <Lnurl lnurl={payment_request} --width=100% />
      <Button on:click={partial(dispatch, "cancel")} class="grey" --width=100%>Back</Button>
    </div>
  {/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 36px 0 40px 0;
  gap: 20px;
}
h1 {
  font-weight: 900;
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}
.font-normal {
  font-size: 18px;
}
.suggestion {
  font-size: 16px;
  width: 402px;
  margin-top: 4px;
  margin-bottom: 8px;
}
.buttons {
  width: 295px;
}
</style>
