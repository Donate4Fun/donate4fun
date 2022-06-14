<script>
  import Header from "../lib/Header.svelte";
  import Donation from "../lib/Donation.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import Invoice from "../lib/Invoice.svelte";
  import api from "../lib/api.js";

  export let donation_id;

  let donation;
  let payment_request;

  const loadDonation = async () => {
    const state_donation = window.history.state;
    if (state_donation && state_donation.id === donation_id) {
      donation = state_donation;
    } else {
      const response = await api.get(`/api/v1/donation/${donation_id}`);
      ({ donation, payment_request } = response);
    }
  }
  function cancel() {
    console.log("invoice cancel");
    invoice = null;
  }
  function close() {
    console.log("donate close");
    donation = null;
  }
  function paid(new_donation) {
    console.log("paid", new_donation);
    donation = new_donation;
  }

</script>

<Header />
{#await loadDonation()}
  <Spinner />Loading...
{:then}
  {#if donation.paid_at}
    <Donation {...donation} on:close={close} />
  {:else}
    <Invoice donation={donation} payment_request={payment_request} on:cancel={cancel} on:paid={paid} />
  {/if}
{/await}
