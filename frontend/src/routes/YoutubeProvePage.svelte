<script>
  import Section from "../lib/Section.svelte";
  import Editable from "../lib/Editable.svelte";
  import CopyButton from "../lib/CopyButton.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import Separator from "../lib/Separator.svelte";
  import LinkedYoutubeChannels from "../lib/LinkedYoutubeChannels.svelte";
  import { me, reloadMe } from "../lib/session.js";
  import { sleep } from "$lib/utils.js";
  import api from "../lib/api.js";
  import title from "../lib/title.js";

  export let navigate;

  async function check() {
    await sleep(5000);
    await api.post("me/youtube/check-ownership");
    await reloadMe();
  }

  async function loadProveMessage() {
    return (await api.get("me/youtube/ownership-message")).message;
  }

  async function useOAuth() {
    const response = await api.get("me/youtube/oauth");
    window.location.href = response.url;
  }

  title.set("Link YouTube channel");
</script>

<Section>
  <main>
    <h1>Prove that you own YouTube channel</h1>
    <ol>
      <li>
        <summary>
          <div class=index></div>
          <span>Copy this comment</span>
        </summary>
        <div>
          {#await loadProveMessage()}
            <Editable message="" />
          {:then message}
            <Editable editable={false} message={message} />
            {#if window.isSecureContext}
              <CopyButton content={message} />
            {/if}
          {/await}
        </div>
      </li>
      <li>
        <summary>
          <div class=index></div>
          <span>Place it under <a href="https://youtu.be/J2Tz2jGQjHE" target=_blank>this video</a> using the account you want to prove ownership for.</span>
        </summary>
      </li>
      <li>
        <summary>
          <div class=index></div>
          <div class=press>
            <span>Press</span>
            <Button on:click={check} class=white --width=195px>
              Check
            </Button>
          </div>
        </summary>
      </li>
    </ol>
    <div>
      {#await $me}
        <Spinner />
      {:then me}
        {#if me.youtube_channels.length}
          <h2>Linked channels</h2>
          <LinkedYoutubeChannels youtube_channels={me.youtube_channels} />
        {:else}
          No comments found, try again.
        {/if}
      {/await}
    </div>
    <Separator>OR</Separator>
    <Button on:click={useOAuth}>Use Google OAuth instead</Button>
    <Infobox>Until this app is verified by Google you will see a warning message. It's OK to bypass it. <a href="https://donate4fun.notion.site/How-to-prove-ownership-of-your-YouTube-channel-c514b950fef74ef8a5886af2926f9392">More info</a></Infobox>
    <Button class="grey" on:click={() => navigate(-1)}>Cancel</Button>
  </main>
</Section>

<style>
main {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 36px 85px 40px 85px;
  width: 640px;
  font-size: 16px;
  line-height: 19px;
}
h1 {
  text-align: center;
  margin: 0;
}
ol {
  display: flex;
  flex-direction: column;
  gap: 44px;
  list-style: none;
  counter-reset: item;
  margin: 0;
  padding: 0;
}
li {
  counter-increment: item;
}
li summary {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 400;
}
li .index {
  width: 40px;
  height: 40px;

  background: linear-gradient(90deg, rgba(249, 240, 62, 0.15) 0%, rgba(157, 237, 162, 0.15) 100%), #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
  border-radius: 50%;
  flex-shrink: 0;
}
li .index::before {
  content: counter(item);
  background: radial-gradient(74.17% 74.17% at 65% 25.83%, rgba(255, 220, 220, 0.58) 0%, rgba(254, 207, 207, 0) 100%) /* warning: gradient uses a rotation that is not supported by CSS and may not behave as expected */, #000000;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 38px;
  text-align: center;
  display: inline-block;
  width: 100%;
  font-weight: 900;
  font-size: 20px;
}
li > div {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 1em;
  margin-top: 24px;
}
.press {
  display: flex;
  align-items: center;
  gap: 12px;
}
h2 {
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.8);
  margin: 0;
}
</style>
