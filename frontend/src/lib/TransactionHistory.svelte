<script>
  import { link } from "svelte-navigator";

  import YoutubeVideo from "$lib/YoutubeVideo.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Donator from "$lib/Donator.svelte";
  import Button from "$lib/Button.svelte";
  import api from "$lib/api.js";
  import { toText } from "$lib/utils.js";

  export let donator_id;
  let donations = [];

  async function load() {
    const newDonations = await api.get(`donations/by-donator/${donator_id}?offset=${donations.length}`);
    donations = [...donations, ...newDonations];
    console.log("donations", donations);
  }
</script>

<div class="table">
  <div class="head">
    <div>Date</div>
    <div>Donatee</div>
    <div>Amount</div>
    <div>Status</div>
  </div>
  {#await load() then}
    {#each donations as donation}
      <a use:link href="/donation/{donation.id}">
        {#if donation.paid_at}
          <Datetime dt={donation.paid_at}/>
        {:else}
          <Datetime dt={donation.created_at}/>
        {/if}
      </a>
      {#if donation.youtube_video}
        <YoutubeVideo video={donation.youtube_video} --gap=16px />
      {:else if donation.youtube_channel}
        <YoutubeChannel channel={donation.youtube_channel} class="ellipsis" linkto=withdraw logo --gap=16px />
      {:else if donation.twitter_account}
        <TwitterAccount account={donation.twitter_account} --image-size=24px --gap=16px />
      {:else if donation.receiver}
        <Donator user={donation.receiver} ellipsis --gap=16px />
      {:else}
        to target
      {/if}
      <Amount amount={toText(donation.amount)}/>
      <div class="status">
        {#if donation.paid_at}
          {#if donation.cancelled_at}
            Cancelled
          {:else if donation.donator.id === donation.receiver?.id}
            Deposited
          {:else if donation.receiver !== null}
            Received
          {:else if donation.claimed_at}
            Claimed
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
{#if donations.length}
  <Button --width=200px --border-width=0 class="white" on:click={load}>Load more</Button>
{/if}

<style>
.table .head {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 109px 199px 83px 45px;
  column-gap: 20px;
  row-gap: 26px;
  align-items: center;
}
.status {
  font-weight: 500;
  font-size: 12px;
  line-height: 15px;
}
</style>
