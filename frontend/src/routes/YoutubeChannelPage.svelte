<script>
  import {link} from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";
  import Donator from "../lib/Donator.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Amount from "../lib/Amount.svelte";
  import Error from "../lib/Error.svelte";
  import Button from "../lib/Button.svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import api from "../lib/api.js";
  import { me } from "../lib/session.js";

  export let channel_id;

  let youtube_channel;
  let sum_donated;
  let donations;
  let error;
  let lnurl;
  let amount;
  let loading = false;
  let showSuccess = false;
  let balance;

  let youtube_channel_url;

  const min_withdraw = 100;

  async function load() {
    loading = true;
    showSuccess = false;
    lnurl = null;
    amount = null;
    try {
      await me.init()
      youtube_channel = await api.get(`youtube-channel/${channel_id}`);
      balance = youtube_channel.balance;
      youtube_channel_url = `https://youtube.com/channel/${youtube_channel.channel_id}`
      donations = await api.get(`donations/by-donatee/${channel_id}`);
      sum_donated = donations.reduce((accum, donation) => accum + donation.amount, 0);
      if (balance >= min_withdraw) {
        if ($me.youtube_channels.includes(channel_id)) {
          const response = await api.get(`youtube-channel/${channel_id}/withdraw`);
          lnurl = response.lnurl;
          amount = response.amount;
          api.subscribe(`youtube-channel/${channel_id}/subscribe`, (msg) => {
            if (msg.status === 'ERROR') {
              error = msg.message;
            }
            lnurl = null;
            showSuccess = true;
          });
        }
      }
    } catch (err) {
      console.log(err)
      error = err.response.data.detail;
    }
    loading = false;
  }
  async function login() {
    loading = true;
    try {
      const response = await api.get(`youtube-channel/${channel_id}/login`);
      window.location.href = response.url;
    } catch (err) {
      error = err.response.data.detail;
    }
    loading = false;
  }
  const loadPromise = load();
</script>

<svelte:head>
  {#await loadPromise then}
  <title>[Donate4Fun] Claim donations for {youtube_channel.title} [youtube_channel.id]</title>
  {/await}
</svelte:head>

<Page>
  <Section class="youtube-channel">
  {#await loadPromise}
    <Loading />
  {:then}
    {#if lnurl}
    <h1>Claim donations</h1>
    {:else}
    <h1>Donations to <a href={youtube_channel_url}>{youtube_channel.title}</a></h1>
    {/if}
    {#if showSuccess}
      <img src="/success.png" class="success" alt="success">
      <div class="donations-claimed">Donations claimed</div>
      <Amount amount={balance} />
      <div class="controls">
        <Button on:click={load} class="close-button grey">Close</Button>
      </div>
    {:else}
    <img class="channel-logo" src={youtube_channel.thumbnail_url} alt="logo">
    <div class="controls">
      {#if lnurl}
        <a href="lightning:{lnurl}"><QRCode value={lnurl}/></a>
        <div class="buttons">
          <a href="lightning:{lnurl}" class="open-in-wallet"><Button>Open in wallet</Button></a>
          <Lnurl lnurl={lnurl} class="lnurl" />
        </div>
        <div class="suggestion">
          Connect wallet and claim your donations with a Wallet like
          <a href="https://getalby.com" target="_blank">Alby</a>, 
          <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>, 
          <a href="https://sbw.app" target="_blank">SBW</a> or 
          <a href="https://blixtwallet.github.io" target="_blank">Blixt</a>
          .
        </div>
        <div class="available">Available BTC to withdraw: <Amount amount={amount}/></div>
      {:else if balance >= min_withdraw}
        <Infobox>You can withdraw donations if the you channel belongs to you. Confirm by login with Google</Infobox>
        <div>Available BTC to withdraw: <Amount amount={balance}/></div>
        <Button loading={loading} on:click={login}>Withdraw — Sign in with Google</Button>
        <div class="annotation">Minimum amount to withdraw is: {min_withdraw} sats</div>
      {:else}
        <Infobox class="red">Minimum amount to withdraw is: {min_withdraw} sats</Infobox>
      {/if}
      <Error message={error}/>
    </div>
    {#if !lnurl}
    <div>Want to support him? <a href="/donate/{channel_id}" use:link>Donate</a></div>
    <div class="table">
      <div class="head">
        <div>Name</div><div>Date</div><div>Amount</div>
      </div>
      <div class="body">
      {#each donations as donation}
        <Donator user={donation.donator} class="ellipsis"/>
        <Datetime dt={donation.paid_at} />
        <Amount amount={donation.amount} />
      {/each}
      </div>
    </div>
    {/if}
  {/if}
  {/await}
  </Section>
</Page>

<style>
:global(.youtube-channel) {
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
.controls :global(.close-button) {
  margin-top: 64px;
  width: 400px;
}
.table {
  font-size: 12px;
}
.head {
  color:  rgba(0, 0, 0, 0.6);
  text-align: left;
}
.body {
  font-weight: 500;
  padding: 0 1em 1em 1em;
}
img {
  width: 72px;
  height: 72px;
}
.buttons {
  width: 295px;
  display: flex;
  flex-direction: column;
}
.controls .open-in-wallet {
  margin-top: 24px;
}
.controls .open-in-wallet :global(button) {
  width: 100%;
}
.controls :global(.lnurl) {
  margin-top: 20px;
  margin-bottom: 32px;
}
.suggestion {
  font-size: 16px;
  text-align: center;
  margin-bottom: 40px;
}
.controls {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.annotation {
  font-size: 14px;
  color: #7C7C7C;
}
.table .head,.table .body {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 99px 99px 99px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
