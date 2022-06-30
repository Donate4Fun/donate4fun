<script>
  import Donation from "../lib/Donation.svelte";
  import Loading from "../lib/Loading.svelte";
  import Invoice from "../lib/Invoice.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import api from "../lib/api.js";

  export let donation_id;
  export let navigate;

  let donation;
  let payment_request;

  const loadDonation = async () => {
    const state_donation = window.history.state;
    if (state_donation && state_donation.id === donation_id) {
      donation = state_donation;
    } else {
      const response = await api.get(`donation/${donation_id}`);
      ({ donation, payment_request } = response);
    }
  }
  function cancel() {
    console.log("invoice cancel");
    navigate(-1);
  }
  function close() {
    console.log("donate close");
    navigate(-1);
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
      <Donation {...donation} on:close={close} />
    {:else}
      <Invoice donation={donation} payment_request={payment_request} on:cancel={cancel} on:paid={paid} />
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
