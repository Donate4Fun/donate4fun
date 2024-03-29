<script>
  import { get } from "svelte/store";
  import { link } from "svelte-navigator";

  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import Loader from "$lib/Loader.svelte";
  import DonationReceiver from "$lib/DonationReceiver.svelte";
  import DonationStatus from "$lib/DonationStatus.svelte";
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
        <DonationReceiver donation={donation} />
        <Amount amount={toText(donation.amount)}/>
        <DonationStatus donation={donation} />
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
.show-more {
  align-self: center;
  margin-bottom: 22px; /* space for shadow */
}
</style>
