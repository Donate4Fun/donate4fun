<script>
  import {link, useResolve} from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donator from "../lib/Donator.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Amount from "../lib/Amount.svelte";
  import Error from "../lib/Error.svelte";
  import Button from "../lib/Button.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Section from "../lib/Section.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import api from "../lib/api.js";
  import { me, reloadMe } from "../lib/session.js";
  import title from "../lib/title.js";

  export let channel_id;

  let youtube_channel;
  let sum_donated;
  let donations;
  let error;
  let showSuccess = false;
  let balance;
  let lnurl;
  let amount;
  let youtube_channel_url;
  let show_more_donations;

  const min_withdraw = 100;

  const resolve = useResolve();

  async function load() {
    showSuccess = false;
    amount = null;
    try {
      await reloadMe();  // force reload to refresh youtube channels
      youtube_channel = await api.get(`youtube-channel/${channel_id}`);
      $title = `Claim donations for ${youtube_channel.title} [${youtube_channel.id}]`
      balance = youtube_channel.balance;
      youtube_channel_url = `https://youtube.com/channel/${youtube_channel.channel_id}`
      donations = await api.get(`donations/by-donatee/${channel_id}`);
      sum_donated = donations.reduce((accum, donation) => accum + donation.amount, 0);
      return await me.get();
    } catch (err) {
      console.log(err)
      error = err.response.data.detail;
    }
  }
  async function link_youtube() {
    const response = await api.get(`link-youtube-channel`);
    window.location.href = response.url;
  }
</script>

<Section>
  <div class="youtube-channel">
    {#await load()}
      <Loading />
    {:then me}
      <h1>Donations to <a href={youtube_channel_url} target=_blank>{youtube_channel.title}</a></h1>
      <ChannelLogo url={youtube_channel.thumbnail_url} />
      <div class="controls">
      {#if balance >= min_withdraw}
        <div class="available">Available BTC to withdraw: <Amount amount={balance} /></div>
        {#if me.youtube_channels.filter(elem => elem.id === channel_id).length > 0}
          <Button class="withdraw" link='{resolve("withdraw")}'>Withdraw</Button>
        {:else}
          <Infobox>You can withdraw donations if the channel belongs to you. Confirm by linking your Youtube channel.</Infobox>
          <Button link="/prove/youtube">Link your Youtube channel</Button>
        {/if}
      {:else}
        <div class="available">Available BTC: <Amount amount={balance} /></div>
        <Infobox class="red">Minimum amount to withdraw: {min_withdraw} sats</Infobox>
      {/if}
        <Button class="want-more white" link={resolve("link")}>Want more donations?</Button>
      </div>
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
    {/await}
  </div>
</Section>

<style>
.youtube-channel {
  padding: 20px 70px 74px;
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
  margin-bottom: 24px;
}
.controls {
  margin-top: 44px;
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.controls :global(button) {
  margin-top: 20px;
  width: 100%;
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
.table .head,.table .body {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 200px 120px 99px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
