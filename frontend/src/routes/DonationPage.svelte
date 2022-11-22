<script>
  import Donation from "$lib/Donation.svelte";
  import Donator from "$lib/Donator.svelte";
  import Loading from "$lib/Loading.svelte";
  import Invoice from "$lib/Invoice.svelte";
  import Section from "$lib/Section.svelte";
  import Button from "$lib/Button.svelte";
  import Amount from "$lib/Amount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import title from "$lib/title.js";
  import api from "$lib/api.js";
  import {notify} from "$lib/notifications.js";
  import {me} from "$lib/session.js";
  import NotFoundPage from "../routes/NotFoundPage.svelte";

  export let donation_id;
  export let navigate;

  let donation;
  let payment_request;
  let targetName;

  async function load() {
    const state_donation = window.history.state;
    if (state_donation && state_donation.id === donation_id) {
      donation = state_donation;
    } else {
      const response = await api.get(`donation/${donation_id}`);
      ({ donation, payment_request } = response);
    }
    if (donation.youtube_channel)
      targetName = donation.youtube_channel.title;
    if (donation.twitter_account)
      targetName = donation.twitter_account.name;
    else if (donation.receiver)
      targetName = donation.receiver.name;
    else
      targetName = "<Unexpected donation target>";

    title.set(`${donation.amount} sats donated to ${targetName}`);
  }

  function paid(event) {
    donation = event.detail;
    if (donation.paid_at && donation.receiver) {
      notify("Success", `You've paid ${donation.amount} sats`, "success");
    }
    title.set(`${donation.amount} sats donated to ${targetName}`);
  }

</script>

<Section>
  <div class="main">
    {#await load()}
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
        {#if donation.youtube_channel}
          <h1>Donate <Amount amount={donation.amount} /> to</h1>
          <YoutubeChannel channel={donation.youtube_channel} />
        {:else if donation.receiver}
          {#await $me then me}
            {#if donation.receiver.id === me.donator.id}
              <h1>Fulfill <Amount amount={donation.amount} /> to your wallet</h1>
            {:else}
              <h1>Donate <Amount amount={donation.amount} /> to <Donator user={donation.receiver} /></h1>
            {/if}
          {/await}
        {/if}
        <Invoice donation={donation} paymentRequest={payment_request} on:cancel={() => navigate(-1)} on:paid={paid} />
      {/if}
    {:catch error}
      <NotFoundPage {error} />
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
