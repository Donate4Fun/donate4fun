<script>
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import Editable from "../lib/Editable.svelte";
  import CopyButton from "../lib/CopyButton.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import Separator from "../lib/Separator.svelte";
  import {me} from "../lib/session.js";
  import api from "../lib/api.js";
  import title from "../lib/title.js";

  let message;
  let proved_channels = null;
  let spin = false;
  export let navigate;

  async function check() {
    spin = true;
    proved_channels = await api.post("me/youtube/check-ownership");
    spin = false;
  }

  async function loadProveMessage() {
    message = (await api.get("me/youtube/ownership-message")).message;
  }

  async function useOAuth() {
    const response = await api.get("me/youtube/oauth");
    window.location.href = response.url;
  }

  title.set("Link YouTube channel");
</script>
<Page>
  <Section>
    <main>
      To prove that you own YouTube channel
      <ol>
        <li>
          <div>
            Copy this comment
            {#await loadProveMessage()}
            <Editable />
            {:then}
            <Editable editable={false} message={message} />
            {#if window.isSecureContext}
            <CopyButton content={message} />
            {/if}
            {/await}
          </div>
        </li>
        <li>
          Place it under <a href="https://youtu.be/J2Tz2jGQjHE" target=_blank>this video</a> <b>using the account you want to prove ownership for</b>.
        </li>
        <li>
          <div>
            <Button on:click={check}>
              {#if spin}
              <Spinner class="spinner" size=20px width=3px />
              {/if}
              <span>Check</span>
            </Button>
          </div>
        </li>
      </ol>
      {#if proved_channels === null}
      {:else if proved_channels.length}
        Found channels:
        <ul>
        {#each proved_channels as channel}
          <li><ChannelLogo url={channel.thumbnail_url} size=28px /><YoutubeChannel {...channel} /></li>
        {/each}
        </ul>
      {:else}
        No comments found, try again.
      {/if}
      <Separator>OR</Separator>
      <Button on:click={useOAuth}>Use Google OAuth instead</Button>
      <Infobox>Until this app is verified by Google you will see a warning message. It's OK to bypass it. <a href="https://donate4fun.notion.site/How-to-prove-ownership-of-your-YouTube-channel-c514b950fef74ef8a5886af2926f9392">More info</a></Infobox>
      <Button class="grey" on:click={() => navigate(-1)}>Cancel</Button>
    </main>
  </Section>
</Page>

<style>
main {
  display: flex;
  flex-direction: column;
  gap: 1em;
  padding: 3em;
  width: 640px;
}
ol {
  display: flex;
  flex-direction: column;
  gap: 1em;
}
ul {
  list-style-type: none;
}
li > div {
  display: flex;
}
ol > li > div {
  flex-direction: column;
  width: 100%;
  gap: 1em;
}
ul > li {
  display: flex;
  align-items: center;
  gap: 0.3em;
}
</style>
