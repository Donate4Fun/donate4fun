<script>
  import {navigate, useResolve} from "svelte-navigator";

  import Section from "../lib/Section.svelte";
  import Input from "../lib/Input.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import api from "../lib/api.js";
  import { me } from "../lib/session.js";

  let donatee;
  let spin = false;
  let error = null;
  const resolve = useResolve();

  async function claim() {
    spin = true;
    error = null;
    try {
      const channel = await api.post(`donatee`, {target: donatee})
      navigate(`/youtube/${channel.id}`);
    } catch (exc) {
      console.error(exc);
      error = exc.error;
    }
    spin = false;
  }
  async function link_youtube() {
    const response = await api.get(`link-youtube-channel`);
    window.location.href = response.url;
  }
</script>

<Section class="claim">
  <h1>Claim donations</h1>
  <span>Check donations for your YouTube channel</span>
  {#await me.init() then}
  {#if $me.youtube_channels.length > 0}
  <div>Linked YouTube channels:</div>
  {/if}
  <ul>
  {#each $me.youtube_channels as channel}
    <li><ChannelLogo url={channel.thumbnail_url} size=28px /><YoutubeChannel {...channel} linkto=withdraw /></li>
  {/each}
  </ul>
  {/await}
  <Infobox>Until this app is verified by Google you will see a warning message. It's OK to bypass it. <a href="">More info</a></Infobox>
  <div class="link"><Button on:click={link_youtube}>Link your Youtube channel</Button></div>
  <form on:submit|preventDefault={claim}>
    <div class=url><Input type=url placeholder="Paste YouTube URL" bind:value={donatee} bind:error={error} logo=url(/static/youtube.svg) required/></div>
    <Button type=submit class="submit white">
      {#if spin}
      <Spinner class="spinner" size=20px width=3px/>
      {/if}
      Check donation
    </Button>
  </form>
</Section>

<style>
@media (max-width: 640px) {
  :global(.claim) {
    width: 100%;
    padding: 20px 36px 20px 24px;
  }
  form {
    margin-top: 42px;
  }
  form .url {
    width: 100%;
    margin-bottom: 24px;
  }
  form :global(.submit) {
    width: 100%;
    margin-bottom: 25px;
  }
}
.link {
  margin-top: 16px;
}
.link,.link > :global(*) {
  width: 100%;
}
h1 {
  margin-top: 0px;
  margin-bottom: 16px;
}
span {
  font-size: 14px;
  line-height: 17px;
}
ul {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
li {
  display: flex;
  align-items: center;
  gap: 8px;
}
@media (min-width: 641px) {
  :global(.claim) {
    width: 640px;
    padding: 36px 36px 40px 36px;
  }
  form {
    display: flex;
    align-items: center;
    margin-top: 38px;
  }
  form .url {
    width: 365px;
    margin-right: 24px;
  }
  form :global(button) {
    white-space: nowrap;
    width: 180px;
  }
}
</style>
