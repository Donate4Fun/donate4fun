<script>
  import { get } from "svelte/store";

  import PaidDonation from "$lib/PaidDonation.svelte";
  import Donator from "$lib/Donator.svelte";
  import Loading from "$lib/Loading.svelte";
  import Invoice from "$lib/Invoice.svelte";
  import Section from "$lib/Section.svelte";
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
    else if (donation.twitter_account)
      targetName = donation.twitter_account.name;
    else if (donation.github_user)
      targetName = donation.github_user.name;
    else if (donation.receiver)
      targetName = donation.receiver.name;
    else
      targetName = "<Unexpected donation target>";

    title.set(`${donation.amount} sats donated to ${targetName}`);
  }

  async function paid(event) {
    const donation_ = event.detail;
    if (donation_.paid_at && donation_.receiver) {
      const me_ = await get(me);
      if (donation.receiver.id === me_.donator.id) {
        notify("Success", `You've fulfilled ${donation_.amount} sats`, "success");
        navigate(`/donator/${me_.donator.id}`);
      } else
        notify("Success", `You've paid ${donation_.amount} sats`, "success");
    } else {
      donation = donation_;
    }
    title.set(`${donation_.amount} sats donated to ${targetName}`);
  }

</script>

<Section>
  <div class="main">
    {#await load()}
      <Loading />
    {:then}
      {#if donation.paid_at}
        <PaidDonation donation={donation} />
      {:else}
        <div class="padding">
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
        </div>
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
@media (max-width: 640px) {
  .main {
    width: 100vw;
  }
}
.padding {
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: center;
}
</style>
