<script>
  import {link} from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";
  import Donator from "../lib/Donator.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Amount from "../lib/Amount.svelte";
  import Error from "../lib/Error.svelte";
  import Button from "../lib/Button.svelte";
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
  let balance;

  let youtube_channel_url;

  const min_withdraw = 100;

  const load = async () => {
    loading = true;
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
            load();
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
</script>

<Page>
  <Section class="youtube-channel">
  {#await load()}
    <Loading />
  {:then}
    <h1>Donations to <a href={youtube_channel_url}>{youtube_channel.title}</a></h1>
    <img src={youtube_channel.thumbnail_url} alt="logo">
    <div class="controls">
      {#if lnurl}
        <a href="lightning:{lnurl}"><QRCode value={lnurl}/></a>
        <div class=lnurl>lightning:{lnurl}</div>
        <div>Available BTC to withdraw: <Amount amount={amount}/></div>
      {:else if balance >= min_withdraw}
        <Infobox>You can withdraw donations if the you channel belongs to you. Confirm by login with Google</Infobox>
        <div>Available BTC to withdraw: <Amount amount={balance}/></div>
        <Button loading={loading} on:click={login}>Withdraw — Sign in with Google</Button>
        <div class="annotation">Minimum amount to withdraw is: {min_withdraw} sats</div>
      {/if}
      <Error message={error}/>
    </div>
    <div>Want to support him? <a href="/donate/{channel_id}" use:link>Donate</a></div>
    <table>
      <thead>
        <tr><th>Name<th>Date<th>Amount</tr>
      </thead>
      <tbody>
      {#each donations as donation}
        <tr><td><Donator user={donation.donator}/><td><Datetime dt={donation.paid_at}/><td><Amount amount={donation.amount}/></tr>
      {/each}
      </tbody>
    </table>
  {/await}
  </Section>
</Page>

<style>
:global(.youtube-channel) {
  padding: 20px 120px 0px 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
h1 {
  text-align: center;
}
table {
  font-size: 12px;
}
thead {
  color:  rgba(0, 0, 0, 0.6);
  text-align: left;
}
tbody {
  font-weight: 500;
}
th, td {
  padding: 0 1em 1em 1em;
}
img {
  width: 72px;
  height: 72px;
}
.lnurl {
  word-break: break-all;
  font-size: 12px;
  line-height: 1em;
  text-align: center;
}
.controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1em;
}
.annotation {
  font-size: 14px;
  color: #7C7C7C;
}
</style>
