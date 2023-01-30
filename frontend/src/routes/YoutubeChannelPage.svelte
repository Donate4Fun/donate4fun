<script>
  import { useResolve, link } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
  import { api, socialDonationsStore } from "$lib/api.js";
  import title from "$lib/title.js";

  export let channel_id;

  const resolve = useResolve();

  async function load() {
    const channel = await api.get(`social/youtube/${channel_id}`);
    $title = `Donate to ${channel.title} YouTube channel`
    return channel
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then channel}
    <Section>
      {#if channel.banner_url}
        <div class="banner" style="background-image: url({channel.banner_url})"></div>
      {/if}
      <div class="content">
        <h1>
          <img alt=youtube src="/static/youtube.svg" height=20>
          Donate to <YoutubeChannel channel={channel} />
          <ChannelLogo url={channel.thumbnail_url} size=44px />
        </h1>
        <PaymentWidget target={{channel_id: channel.id}} on:paid={load} />
        <a use:link href={resolve("owner")}>This is my channel</a>
      </div>
    </Section>

    <div class="details">
      <DonationsTable donations={socialDonationsStore("youtube", channel.id)} />
    </div>
  {/await}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 32px;
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
.banner {
  width: 100%;
  height: 102px;
  background-repeat: no-repeat;
  background-size: 100%;
  background-position: center;
  border-top-left-radius: inherit;
  border-top-right-radius: inherit;
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
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 640px;
}
</style>
