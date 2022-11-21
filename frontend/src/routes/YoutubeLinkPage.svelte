<script>
  import { get } from "svelte/store";
  import Section from "$lib/Section.svelte";
  import Button from "$lib/Button.svelte";
  import CopyButton from "$lib/CopyButton.svelte";
  import Editable from "$lib/Editable.svelte";
  import Loading from "$lib/Loading.svelte";
  import { youtube_channel_url, webOrigin } from "$lib/utils.js";
  import api from "$lib/api.js";
  import title from "$lib/title.js";

  export let channel_id;
  export let navigate;

  let youtube_channel;
  let message;

  async function load() {
    youtube_channel = await api.get(`youtube/channel/${channel_id}`);
    message = `⚡ Donate4Fun to me here ${get(webOrigin)}/d/${youtube_channel.channel_id}`;
    $title = `Collect donations for ${youtube_channel.title} with Bitcoin Lightning`;
  }
</script>

{#await load()}
  <Loading />
{:then}
  <Section>
    <div class="youtube-link">
      <h1>Hey! Do you want to get more donations?</h1>
      <div class="call-to-action">Add this link to your Youtube channel and video descriptions.
        <a href="https://donate4fun.notion.site/How-to-add-Donate4-Fun-link-to-YouTube-1999f6f4318c4702aff37840b13e7315">How to do this?</a>
      </div>
      <Editable bind:message={message} />
      <CopyButton bind:content={message} />
      <Button link={youtube_channel_url(youtube_channel.channel_id)} target=_blank>Edit your YouTube channel...</Button>
      <Button class="grey" on:click={() => navigate(-1)}>Back</Button>
    </div>
  </Section>
{/await}

<style>
.youtube-link {
  width: 640px;
  padding: 36px 72px 45px 72px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.youtube-link > h1,div {
  text-align: center;
}
</style>
