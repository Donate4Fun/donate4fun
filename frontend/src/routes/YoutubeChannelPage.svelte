<script>
  import {link} from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";
  import Donator from "../lib/Donator.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Amount from "../lib/Amount.svelte";
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
  import Error from "../lib/Error.svelte";
  import Button from "../lib/Button.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Section from "../lib/Section.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import api from "../lib/api.js";
  import { me } from "../lib/session.js";

  export let channel_id;

  let youtube_channel;
  let sum_donated;
  let sum_unclaimed;
  let donations;
  let error;
  let lnurl;
  let amount;
  let loading = false;
  const min_claim_limit = 100;
  $: isClaimAllowed = sum_unclaimed >= min_claim_limit;

  const load = async () => {
    await me.init()
    youtube_channel = await api.get(`youtube-channel/${channel_id}`);
    donations = await api.get(`donations/by-donatee/${channel_id}`);
    sum_donated = donations.reduce((accum, donation) => accum + donation.amount, 0);
    sum_unclaimed = donations.reduce((accum, donation) => {
      if (!donation.claimed_at) {
        return accum + donation.amount;
      } else {
        return accum;
      }
    }, 0);
  }
  async function withdraw() {
    loading = true;
    try {
      const response = await api.get(`youtube-channel/${channel_id}/withdraw`);
      lnurl = response.lnurl;
      amount = response.amount;
    } catch (err) {
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
</script>

<Header/>
<Section class="youtube-channel-section">
{#await load()}
  <Loading />
{:then}
  <YoutubeChannel {...youtube_channel}/>
  <div>Total donated: <Amount amount={sum_donated}/>.</div>
  <div>Unclaimed: <Amount amount={sum_unclaimed}/>.</div>
  <div class="action-button">
    {#if lnurl}
      <QRCode value={lnurl} />
      <div class=lnurl>lightning:{lnurl}</div>
      <Amount amount={amount}/>
    {:else if $me.youtube_channels.includes(channel_id)}
      <Button loading={loading} disabled={!isClaimAllowed} on:click={withdraw}>Withdraw</Button>
    {:else}
      <Button loading={loading} on:click={login}>Login to YouTube</Button>
    {/if}
    <Error message={error}/>
  </div>
  <div>Want to support him? <a href="/donate/{channel_id}" use:link>Donate</a></div>
  <table>
    <thead>
      <tr><th>Whom<th>Paid at<th>How much<th>Withdrawed at</tr>
    </thead>
    <tbody>
    {#each donations as donation}
      <tr><td><Donator user={donation.donator}/><td><Datetime dt={donation.paid_at}/><td><Amount amount={donation.amount}/><td><Datetime dt={donation.claimed_at}/></tr>
    {/each}
    </tbody>
  </table>
{/await}
</Section>
<Footer/>

<style>
table {
  font-size: 12px;
}
.lnurl {
  word-break: break-all;
  font-size: 12px;
  line-height: 1em;
}
.donate-button {
  display: flex;
  flex-direction: column;
}
:global(.youtube-channel-section) {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 30em;
  gap: 1em;
}
</style>
