<script>
  import { link, useResolve } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
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
    $title = `Donate to ${channel.title} YouTube channel`
    donations = await api.get(`${baseUrl}/donations/by-donatee`);
    return await me.get();
  }

  async function claim() {
    await api.post(`${baseUrl}/transfer`);
    await load();
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then me}
    <Section>
      {#if channel.banner_url}
        <div class="banner" style="background-image: url({channel.banner_url})"></div>
      {/if}
      <div class="youtube-channel">
        <h1>
          <img alt=youtube src="/static/youtube.svg" width=20>
          Donate to <YoutubeChannel channel={channel} />
          <ChannelLogo url={channel.thumbnail_url} size=44px />
        </h1>
        <PaymentWidget target={{channel_id: channel.id}} on:paid={load} />
      </div>
    </Section>

    <div class="details">
      <div class="controls">
        {#if channel.is_my}
          <div class="available">Available to claim: <Amount amount={channel.balance} /></div>
          {#if me.connected}
            <Button disabled={channel.balance === 0} on:click={claim}>Take donations</Button>
          {:else}
            <Button link={resolve('/login')}>Take donations</Button>
          {/if}
        {:else}
          <Button class="white" link="/youtube/prove">This is my channel</Button>
        {/if}
        <Button class="white" link={resolve("link")}>Want more donations?</Button>
      </div>
      <DonationsTable donations={donations} />
    </div>
  {/await}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.youtube-channel {
  padding: 36px 70px 74px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
.banner {
  width: 100%;
  height: 102px;
  background-repeat: no-repeat;
  background-size: 100%;
  background-position: center;
  border-top-left-radius: inherit;
  border-top-right-radius: inherit;
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
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 640px;
}
.controls {
  display: flex;
  gap: 20px;
  flex-direction: column;
  align-items: center;
}
</style>
