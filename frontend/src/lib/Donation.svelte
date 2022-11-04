<script>
  import { createEventDispatcher } from 'svelte';
  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import Loading from "$lib/Loading.svelte";
  import Amount from "$lib/Amount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Editable from "$lib/Editable.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import { me } from "$lib/session.js";
  import { copy, youtube_video_url, youtube_channel_url } from "$lib/utils.js";

  const dispatch = createEventDispatcher();

  export let donation;

  let message = `Hi! I like your video! I’ve donated you ${donation.amount} sats. You can take it on "donate 4 fun"`;

  function copyAndShare() {
    copy(message);
    let url;
    if (donation.youtube_video !== null) {
      url = youtube_video_url(donation.youtube_video.video_id);
    } else {
      url = youtube_channel_url(donation.youtube_channel.channel_id);
    }
    window.open(url, '_blank').focus();
  }
</script>

<main>
{#await $me}
  <Loading/>
{:then me}
  <ChannelLogo url={donation.youtube_channel.thumbnail_url} size=72px />
  <div class="header">
    <p>Great! You've sent <Amount amount={donation.amount}/> to</p>
    <YoutubeChannel channel={donation.youtube_channel}/>
  </div>
  {#if me.donator.id === donation.donator_id}
    <Infobox>Copy and share the message with the link or just tell {donation.youtube_channel.title} to receive the donation here at «Donate4Fun»</Infobox>
    <div>
      {#if donation.youtube_video}
        Now leave a comment on <a href="{youtube_video_url(donation.youtube_video.video_id)}" target=_blank>his video</a> to make him know of donation:
      {:else}
        Now leave a comment on his video to make him know of donation:
      {/if}
    </div>
    <ol>
      <li>Press "Copy and Share" - comment will be copied to clipboard and YouTube video tab will open</li>
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
  gap: 32px;
  padding: 44px 84px 40px 84px;
}
.header {
  display: flex;
  flex-direction: column;
  align-items: center;

  font-weight: 900;
  font-size: 24px;
}
main > :global(button) {
  width: 402px;
  height: 44px;
}
</style>
