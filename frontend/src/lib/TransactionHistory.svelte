<script>
  import { get } from "svelte/store";

  import { link } from "svelte-navigator";
  import TwitterBrand from "svelte-awesome-icons/TwitterBrand.svelte";
  import YoutubeBrand from "svelte-awesome-icons/YoutubeBrand.svelte";

  import YoutubeVideo from "$lib/YoutubeVideo.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Donator from "$lib/Donator.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import Loader from "$lib/Loader.svelte";
  import api from "$lib/api.js";
  import { toText } from "$lib/utils.js";
  import { me } from "$lib/session.js";

  export let donator_id;
  export let direction;

  let donations = [];
  let showMore = false;

  async function load() {
    const newDonations = await api.get(`donations/by-donator/${donator_id}/${direction}?offset=${donations.length}`);
    showMore = newDonations.length !== 0;
    donations = [...donations, ...newDonations];
  }

  async function firstLoad() {
    await load();
    return await get(me);
  }
</script>

<div class="container">
  <div class="table">
    <div class="head">
      <div>Date</div>
      <div>Receiver</div>
      <div>Amount</div>
      <div>Status</div>
    </div>
    {#await firstLoad()}
      <Loader --size=4em />
    {:then me}
      {#each donations as donation (donation.id)}
        {#if donation.receiver}
          <Datetime dt={donation.paid_at}/>
        {:else}
          <a target="_blank" href="/donation/{donation.id}">
            {#if donation.paid_at}
              <Datetime dt={donation.paid_at}/>
            {:else}
              <Datetime dt={donation.created_at}/>
            {/if}
          </a>
        {/if}
        <div class="receiver">
          {#if donation.youtube_video}
            <div class="noshrink"><YoutubeBrand height=20 width=24 color=red /></div>
            <YoutubeVideo video={donation.youtube_video} linkto=channel target="blank" --gap=8px />
          {:else if donation.youtube_channel}
            <div class="noshrink"><YoutubeBrand height=20 width=24 color=red /></div>
            <YoutubeChannel channel={donation.youtube_channel} class="ellipsis" linkto=withdraw target="blank" logo --gap=8px />
          {:else if donation.twitter_account}
            <div class="noshrink"><TwitterBrand width=24 color=#2E6CFF /></div>
            <TwitterAccount account={donation.twitter_account} --image-size=24px --gap=8px target="blank" />
          {:else if donation.receiver}
            <div class="noshrink"><img src="/static/D.svg" height=20 width=24 alt="donate4.fun"></div>
            <Donator user={donation.receiver} ellipsis --gap=8px target="blank" />
          {:else}
            to target
          {/if}
        </div>
        <Amount amount={toText(donation.amount)}/>
        <div class="status">
          {#if donation.paid_at}
            {#if donation.cancelled_at}
              <span class="cancelled">Cancelled</span>
            {:else if donation.donator.id === donation.receiver?.id}
              Deposited
            {:else if donation.receiver?.id === me.donator.id}
              Received
            {:else if donation.receiver}
              Sent
            {:else if donation.lightning_address}
              <span class="success">Via ⚡@</span>
            {:else if donation.claimed_at}
              <span class="success">Claimed</span>
            {:else}
              Pending
            {/if}
          {:else}
            Unpaid
          {/if}
        </div>
      {/each}
    {/await}
  </div>
  {#if showMore}
    <div class="show-more">
      <BaseButton
        --width=136px
        --border-color="rgba(46, 108, 255, 0.15)"
        --background-image="linear-gradient(white, white)"
        on:click={load}
      >Show more</BaseButton>
    </div>
  {/if}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.table .head {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 109px 199px 83px 60px;
  column-gap: 20px;
  row-gap: 26px;
  align-items: center;
}
.noshrink {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.receiver {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status {
  font-weight: 500;
  font-size: 12px;
  line-height: 15px;
}
.cancelled {
  color: #FF472E;
}
.success {
  color: #19B400;
}
.show-more {
  align-self: center;
  margin-bottom: 22px; /* space for shadow */
}
</style>
