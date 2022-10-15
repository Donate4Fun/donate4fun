<script>
  import Donation from "../lib/Donation.svelte";
  import Donator from "../lib/Donator.svelte";
  import Loading from "../lib/Loading.svelte";
  import Invoice from "../lib/Invoice.svelte";
  import Section from "../lib/Section.svelte";
  import Button from "../lib/Button.svelte";
  import title from "../lib/title.js";
  import api from "../lib/api.js";
  import {notify} from "../lib/notifications.js";
  import {me} from "../lib/session.js";

  export let donation_id;
  export let navigate;

  let donation;
  let payment_request;
  let target;

  async function load() {
    await $me.loaded;
    const state_donation = window.history.state;
    if (state_donation && state_donation.id === donation_id) {
      donation = state_donation;
    } else {
      const response = await api.get(`donation/${donation_id}`);
      ({ donation, payment_request } = response);
      if (donation.youtube_channel)
        target = donation.youtube_channel.title;
      else if (donation.receiver)
        target = donation.receiver.name;
      else
        target = "<Unexpected donation target>";
    }
  }

  function paid(event) {
    console.log("paid", event.detail);
    donation = event.detail;
    if (donation.paid_at && donation.receiver) {
      navigate(`/donator/${donation.receiver.id}`);
      notify("Success", `You've paid ${donation.amount} sats`, "success");
    }
  }

  const loadPromise = load();
</script>

<svelte:head>
  {#await loadPromise then}
  <title>Donate {donation.amount} sats to {target} [{donation.id}]</title>
  {/await}
</svelte:head>

<Section>
  <div class="main">
    {#await loadPromise}
      <Loading />
    {:then}
      {#if donation.paid_at}
        {#if !donation.receiver}
          <Donation donation={donation} on:close={() => navigate(-1)} />
        {:else}
          <div class="flex-column">
            {#await $me then me}
              {#if donation.receiver.id === me.donator.id}
                You successfuly fulfilled your balance.
              {:else}
                You successfuly donated to <Donator user={donation.receiver} />.
              {/if}
            {/await}
            <Button class=white on:click={() => navigate(-2)}>Close</Button>
          </div>
        {/if}
      {:else}
        <Invoice donation={donation} payment_request={payment_request} on:cancel={() => navigate(-1)} on:paid={paid} />
      {/if}
    {/await}
  </div>
</Section>

<style>
.main {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 640px;
}
</style>
