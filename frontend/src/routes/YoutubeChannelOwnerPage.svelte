<script>
  import { link, useResolve } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
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
    $title = `Manage ${channel.title} YouTube channel`
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
      <div class="youtube-channel">
        <h1>
          <img alt=youtube src="/static/youtube.svg" width=20>
          <YoutubeChannel channel={channel} />
          <ChannelLogo url={channel.thumbnail_url} size=44px />
        </h1>
      </div>
      <div class="controls">
        {#if channel.is_my}
          <div class="available">Available to claim: <Amount amount={channel.balance} /></div>
          {#if me.connected}
            <Button disabled={channel.balance === 0} on:click={claim}>Collect donations</Button>
          {:else}
            <Button link='/login'>Login to collect donations</Button>
          {/if}
        {:else}
          <Button class="white" link="/youtube/prove">This is my channel</Button>
        {/if}
        <Button class="white" link={resolve("../link")}>Want more donations?</Button>
      </div>
    </Section>
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
h1 {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 22px;
  font-weight: 400;
}
.controls {
  display: flex;
  gap: 20px;
  flex-direction: column;
  align-items: center;
}
</style>
