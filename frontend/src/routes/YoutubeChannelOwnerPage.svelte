<script>
  import { link, useResolve, navigate } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import { api } from "$lib/api.js";
  import { me } from "$lib/session.js";
  import title from "$lib/title.js";

  export let channel_id;

  let channel;
  let donations;
  $: baseUrl = `youtube/channel/${channel_id}`;

  const resolve = useResolve();

  async function load() {
    channel = await api.get(baseUrl);
    if (!channel.is_my)
      navigate('/youtube/prove', {replace: true});
    $title = `Manage ${channel.title} YouTube channel`
  }

  async function claim() {
    await api.post(`${baseUrl}/transfer`);
    await load();
  }

  async function loadDonations() {
    return await api.get(`${baseUrl}/donations/by-donatee`);
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then}
    <Section>
      <div class="content">
        <h1>
          <img alt=youtube src="/static/youtube.svg" height=20>
          <YoutubeChannel channel={channel} />
          <ChannelLogo url={channel.thumbnail_url} size=44px />
        </h1>
        <div class="controls">
          <div class="available">Available to claim:</div>
          <div class="amounts">
            <Amount amount={channel.balance} />
            <FiatAmount amount={channel.balance} />
          </div>
          <div class="buttons">
            {#await $me then me}
              {#if me.connected}
                <Button disabled={channel.balance === 0} on:click={claim} --border-width=0>Collect</Button>
              {:else}
                <Button link='/login' --border-width=0>Login to collect</Button>
              {/if}
            {/await}
          </div>
          <div class="links">
            <a use:link href={resolve("../link")}>Want more donations?</a>
            <a use:link href={resolve("..")}>Public page</a>
          </div>
        </div>
      </div>
    </Section>

    <div class="details">
      {#await loadDonations() then donations}
        <DonationsTable donations={donations} />
      {/await}
    </div>
  {/await}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 64px;
}
.content {
  padding: 40px 70px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
.content a {
  font-weight: 600;
  font-size: 14px;
  line-height: 20px;
}
h1 {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 22px;
  font-weight: 400;
}
.amounts {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}
.controls {
  display: flex;
  gap: 32px;
  flex-direction: column;
  align-items: center;
}
.buttons {
  width: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}
.links {
  display: flex;
  justify-content: space-between;
  width: 300px;
}
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 640px;
}
</style>
