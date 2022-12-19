<script>
  import { onMount, onDestroy } from 'svelte';
  import { link, useNavigate } from "svelte-navigator";

  import BaseButton from "$lib/BaseButton.svelte";
  import Section from "$lib/Section.svelte";
  import Loading from "$lib/Loading.svelte";
  import Donator from "$lib/Donator.svelte";
  import TwitterDonation from "$lib/TwitterDonation.svelte";
  import YoutubeDonation from "$lib/YoutubeDonation.svelte";
  import { me } from "$lib/session.js";
  import api from "$lib/api.js";

  export let donation;
  let navigate = useNavigate();

  async function cancel() {
    await api.post(`donation/${donation.id}/cancel`);
  }

  let ws;
  onDestroy(async () => {
    await ws?.close();
  });

  async function subscribe() {
    ws = api.subscribe(`donation:${donation.id}`, { autoReconnect: false });
    ws.on("notification", async (notification) => {
      await ws.close();
      ws = null;
      donation = (await api.get(`donation/${donation.id}`)).donation;
    });
    await ws.ready();
  }

  onMount(subscribe);
</script>

<div class="container">
  <div class="cancelled-container" class:cancelled={donation.cancelled_at !== null}>
    {#if donation.youtube_channel}
      <YoutubeDonation {donation} />
    {:else if donation.twitter_account}
      <TwitterDonation {donation} />
    {/if}
  </div>
  {#if donation.cancelled_at}
    <div class="status-message">
      Donation cancelled
    </div>
  {:else if donation.claimed_at}
    <div class="status-message">
      Donation claimed
    </div>
  {:else}
    {#await $me then me}
      {#if donation.donator.id === me.donator.id}
        <BaseButton
          --background-color="white"
          --border-width="2px"
          --border-color="#EDEDED"
          --text-color="#FF4B4B"
          --shadow="none"
          on:click={cancel}
        >Cancel donation</BaseButton>
      {/if}
    {/await}
  {/if}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding: 58px;
}
@media (max-width: 640px) {
  .container {
    padding: 48px 32px;
    width: 100%;
  }
}
@media (min-width: 641px) {
  .container {
    padding: 48px 120px;
    width: 100%;
  }
}
.cancelled-container {
  width: 100%;
}
.cancelled {
  opacity: 0.5;
}
.status-message {
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
}
</style>
