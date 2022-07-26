<script>
  import {createEventDispatcher, onDestroy} from "svelte";
  import {link, useResolve, navigate} from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";
  import Donator from "../lib/Donator.svelte";
  import Amount from "../lib/Amount.svelte";
  import Error from "../lib/Error.svelte";
  import Button from "../lib/Button.svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import title from "../lib/title.js";
  import api from "../lib/api.js";

  export let channel_id;

  let youtube_channel;
  let lnurl;
  let amount;
  let loading = false;
  let showSuccess = false;

  let youtube_channel_url;

  const min_withdraw = 100;
  const dispatch = createEventDispatcher();
  const resolve = useResolve();
  let unsubscribe = null;
  onDestroy(() => {
    if (unsubscribe !== null) {
      unsubscribe();
    }
  });

  async function load() {
    const base = `youtube-channel/${channel_id}`;
    youtube_channel = await api.get(base);
    try {
      const response = await api.get(`${base}/withdraw`);
      lnurl = response.lnurl;
      amount = response.amount;
      title.set(`Withdraw ${amount} sats for ${youtube_channel.title} [${youtube_channel.id}]`);
      unsubscribe = await api.subscribe(`withdrawal:${channel_id}`, (msg) => {
        unsubscribe();
        if (msg.status === 'ERROR') {
          notify(msg.message);
        }
        showSuccess = true;
      });
    } catch (err) {
      console.log(err);
      if (err.response.status === 403 || (err.response.data.status === 'error' && err.response.data.type === 'ValidationError'))
        navigate(".");
    }
  }
</script>

<Page>
  <Section class="withdraw">
  {#await load()}
    <Loading />
  {:then}
    <h1>Withdraw <Amount amount={amount} /></h1>
  {#if showSuccess}
    <img src="/static/success.png" class="success" alt="success">
    <div class="donations-claimed">Donations claimed</div>
    <div class="buttons success">
      <Button link={resolve("../link")}>Want more donations?</Button>
      <Button class="grey" on:click={() => navigate(-1)}>Close</Button>
    </div>
  {:else}
    <ChannelLogo url={youtube_channel.thumbnail_url} />
    {#if lnurl}
      <a class="qrcode" href="lightning:{lnurl}"><QRCode value={lnurl} /></a>
      <div class="buttons">
        <a href="lightning:{lnurl}" class="open-in-wallet"><Button>Open in wallet</Button></a>
        <Lnurl lnurl={lnurl} class="lnurl" />
        <Button class="grey" on:click={() => navigate(-1)}>Cancel</Button>
      </div>
      <div class="suggestion">
        Don’t have a wallet? Download wallet and claim your donations with a Wallet Like
        <a href="https://getalby.com" target="_blank">Alby</a>, 
        <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
        <a href="https://sbw.app" target="_blank">SBW</a> or 
        <a href="https://blixtwallet.github.io" target="_blank">Blixt</a>
        .
      </div>
    {/if}
  {/if}
  {/await}
  </Section>
</Page>

<style>
:global(.withdraw) {
  padding: 20px 120px 74px 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
h1 {
  text-align: center;
  font-weight: 900;
  font-size: 24px;
}
img.success {
  width: 120px;
  height: 120px;
}
.donations-claimed {
  margin-top: 20px;
  margin-bottom: 14px;
  font-weight: 900;
  font-size: 24px;
}
.qrcode {
  margin-top: 16px;
}
.buttons {
  width: 310px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.buttons.success {
  gap: 20px;
  margin-top: 66px;
  width: 400px;
}
.buttons .open-in-wallet {
  margin-top: 24px;
  width: 100%;
}
.buttons :global(.lnurl) {
  margin-top: 20px;
  margin-bottom: 32px;
  width: 100%;
}
.buttons :global(button) {
  width: 100%;
}
.suggestion {
  font-size: 16px;
  text-align: center;
}
</style>
