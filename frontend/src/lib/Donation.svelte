<script>
  import { createEventDispatcher } from 'svelte';
  import Button from "../lib/Button.svelte";
  import Section from "../lib/Section.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import Loading from "../lib/Loading.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Editable from "../lib/Editable.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import { me } from "../lib/session.js";
  import { copy, youtube_video_url, youtube_channel_url } from "../lib/utils.js";

  const dispatch = createEventDispatcher();

  export let amount;
  export let donator_id;
  export let id;
  export let trigger;
  export let paid_at;
  export let created_at;
  export let youtube_channel;
  export let youtube_video;

  let message = `Hi! I like your video! I’ve donated you ${amount} sats. You can take it on "donate 4 fun"`;

  function copyAndShare() {
    copy(message);
    let url;
    if (youtube_video !== null) {
      url = youtube_video_url(youtube_video.video_id);
    } else {
      url = youtube_channel_url(youtube_channel.channel_id);
    }
    window.open(url, '_blank').focus();
  }
</script>

<main>
{#await me.init()}
  <Loading/>
{:then}
  <ChannelLogo url={youtube_channel.thumbnail_url} size=72px />
  <div class="header">Great! You've sent <Amount amount={amount}/> to <YoutubeChannel {...youtube_channel}/></div>
  {#if $me.donator.id === donator_id}
  <Infobox>Copy and share the message with the link or just tell {youtube_channel.title} to receive the donation here at «Donate4Fun»</Infobox>
  <call-to-action>
  {#if youtube_video}
  Now leave a comment on <a href="{youtube_video_url(youtube_video.video_id)}" target=_blank>his video</a> to make him know of donation:
  {:else}
  Now leave a comment on his video to make him know of donation:
  {/if}
  </call-to-action>
  <ol>
    <li>Press "Copy and Share" - commend will be copied to clipboard and YouTube video tab will open</li>
    <li>Scroll to comments section and focus "Add a comment..." field</li>
    <li>Paste a comment from clipboard and post it</li>
  </ol>
  <Editable class=message message={message} />
  <Button on:click={copyAndShare} class="copy-button">Copy and Share</Button>
  <Button on:click={() => dispatch("close")} class="grey">Back</Button>
  {/if}
{/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 44px 84px 40px 84px;
}
main > .header {
  margin-top: 16px;
  margin-bottom: 22px;
}
main > :global(.message) {
  margin-top: 52px;
  margin-bottom: 28px;
}
main > :global(.copy-button) {
  margin-bottom: 20px;
}
.youtube_channel_thumbnail {
  width: 3em;
  height: 3em;
}
.header {
  font-weight: 900;
  font-size: 24px;
  text-align: center;
}
main > :global(button) {
  width: 402px;
  height: 44px;
}
</style>
