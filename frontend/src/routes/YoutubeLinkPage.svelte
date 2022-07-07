<script>
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import Button from "../lib/Button.svelte";
  import CopyButton from "../lib/CopyButton.svelte";
  import Editable from "../lib/Editable.svelte";
  import Loading from "../lib/Loading.svelte";
  import {youtube_studio_url} from "../lib/utils.js";
  import api from "../lib/api.js";

  export let channel_id;
  export let navigate;

  let message = "⚡ Donate4Fun to me here https://donate4.fun/donate/UCYoGg9ZHG";
  let youtube_channel;

  async function load() {
    youtube_channel = await api.get(`youtube-channel/${channel_id}`);
  }
</script>

<Page>
  {#await load()}
  <Loading />
  {:then}
  <Section class="youtube-link">
    <h1>Want to get more donations?
      <a href={youtube_studio_url(youtube_channel.channel_id)} target=_blank>
        Add this link to your Youtube channel and video descriptions
      </a>
    </h1>
    <Editable bind:message={message} />
    <CopyButton bind:content={message} />
    <Button class="grey" on:click={() => navigate(-1)}>Close</Button>
  </Section>
  {/await}
</Page>

<style>
:global(.youtube-link) {
  width: 640px;
  padding: 36px 72px 45px 72px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
h1 {
  text-align: center;
}
</style>
