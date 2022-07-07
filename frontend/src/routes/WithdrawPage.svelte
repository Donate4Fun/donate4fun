<script>
  import {createEventDispatcher} from "svelte";
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
  import api from "../lib/api.js";

  export let channel_id;

  let youtube_channel;
  let lnurl;
  let amount;
  let loading = false;
  let showSuccess = true;

  let youtube_channel_url;

  const min_withdraw = 100;
  const dispatch = createEventDispatcher();
  const resolve = useResolve();

  async function load() {
    const base = `youtube-channel/${channel_id}`;
    youtube_channel = await api.get(base);
    try {
      const response = await api.get(`${base}/withdraw`);
      lnurl = response.lnurl;
      amount = response.amount;
      api.subscribe(`${base}/subscribe`, (msg) => {
        if (msg.status === 'ERROR') {
          notify(msg.message);
        }
        showSuccess = true;
      });
    } catch (err) {
      if (err.status === 'error' && err.type === 'ValidationError')
        navigate("..");
    }
  }
  const loadPromise = load();
</script>

<svelte:head>
  {#await loadPromise then}
  <title>[Donate4Fun] Withdraw {amount} sats for {youtube_channel.title} [youtube_channel.id]</title>
  {/await}
</svelte:head>

<Page>
  <Section class="withdraw">
  {#await loadPromise}
    <Loading />
  {:then}
    <h1>Withdraw <Amount amount={amount} /></h1>
  {#if showSuccess}
    <img src="/success.png" class="success" alt="success">
    <div class="donations-claimed">Donations claimed</div>
    <div class="buttons">
      <Button link={resolve("link")}>Want more donations?</Button>
      <Button class="grey" on:click={() => navigate(-1)}>Close</Button>
    </div>
  {:else}
    <img class="channel-logo" src={youtube_channel.thumbnail_url} alt="logo">
    {#if lnurl}
      <a href="lightning:{lnurl}"><QRCode value={lnurl} /></a>
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
.channel-logo {
  width: 72px;
  margin-bottom: 24px;
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
img {
  width: 72px;
  height: 72px;
}
.buttons {
  width: 295px;
  display: flex;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.button :global(.close-button) {
  margin-top: 64px;
  width: 400px;
}
.buttons .open-in-wallet {
  margin-top: 24px;
}
.buttons .open-in-wallet :global(button) {
  width: 100%;
}
.controls :global(.lnurl) {
  margin-top: 20px;
  margin-bottom: 32px;
}
.suggestion {
  font-size: 16px;
  text-align: center;
}
</style>
