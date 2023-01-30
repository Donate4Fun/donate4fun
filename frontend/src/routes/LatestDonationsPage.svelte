<script>
  import Section from "$lib/Section.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import DonationReceiver from "$lib/DonationReceiver.svelte";
  import DonationStatus from "$lib/DonationStatus.svelte";
  import Amount from "$lib/Amount.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Loader from "$lib/Loader.svelte";
  import Donator from "$lib/Donator.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import { apiListStore, api } from "$lib/api.js";
  import { toText } from "$lib/utils.js";

  const donations = apiListStore(
    'donations/latest',
    async (itemId) => (await api.get(`donation/${itemId}`)).donation,
    'donations',
  );
</script>

<Section --padding=40px --width=fit-content>
  <h1>Latest donations</h1>

  <div class="table">
    <div class="head">
      <div>Date</div>
      <div>Sender</div>
      <div>Receiver</div>
      <div>Amount</div>
      <div>Status</div>
    </div>
    {#if $donations === null}
      <Loader --size=4em />
    {:else}
      {#each $donations as donation (donation.id)}
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
        <Donator user={donation.donator} ellipsis />
        <DonationReceiver donation={donation} />
        <Amount amount={toText(donation.amount)}/>
        <DonationStatus donation={donation} />
      {/each}
    {/if}
  </div>
  {#if $donations !== null}
    <div class="show-more">
      <BaseButton
        --width=136px
        --border-color="rgba(46, 108, 255, 0.15)"
        --background-image="linear-gradient(white, white)"
        on:click={donations.loadMore}
      >Show more</BaseButton>
    </div>
  {/if}
</Section>

<style>
.table .head {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 109px 140px 199px 83px 60px;
  column-gap: 20px;
  row-gap: 26px;
  align-items: center;
  overflow: scroll;
  width: 100%;
}
.show-more {
  align-self: center;
  margin-bottom: 22px; /* space for shadow */
}
</style>
