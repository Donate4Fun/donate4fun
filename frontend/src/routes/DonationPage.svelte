<script>
  import Donation from "../lib/Donation.svelte";
  import Loading from "../lib/Loading.svelte";
  import Invoice from "../lib/Invoice.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import title from "../lib/title.js";
  import api from "../lib/api.js";

  export let donation_id;
  export let navigate;

  let donation;
  let payment_request;

  async function loadDonation() {
    const state_donation = window.history.state;
    if (state_donation && state_donation.id === donation_id) {
      donation = state_donation;
    } else {
      const response = await api.get(`donation/${donation_id}`);
      ({ donation, payment_request } = response);
    }
    title.set(`Donate ${donation.amount} sats to ${donation.youtube_channel.title} [${donation.id}]`);
  }
  function paid(event) {
    console.log("paid", event.detail);
    donation = event.detail;
  }
</script>

<Page>
  <Section class="main-section">
  {#await loadDonation()}
    <Loading />
  {:then}
    {#if donation.paid_at}
      <Donation {...donation} on:close={() => navigate(-1)} />
    {:else}
      <Invoice donation={donation} payment_request={payment_request} on:cancel={() => navigate(-1)} on:paid={paid} />
    {/if}
  {/await}
  </Section>
</Page>

<style>
:global(.main-section) {
  align-items: center;
  width: 640px;
}
</style>
