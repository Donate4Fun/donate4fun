<script>
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import Editable from "$lib/Editable.svelte";
  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import Amount from "$lib/Amount.svelte";
  import ModalPopup from "$lib/ModalPopup.svelte";
  import Donator from "$lib/Donator.svelte";
  
  import { me } from "$lib/session.js";
  import { copy, youtube_video_url, youtube_channel_url } from "$lib/utils.js";

  export let donation;

  let message = `Hi! I like your video! I’ve donated you ${donation.amount} sats. You can take it on "donate 4 fun"`;
  let showSharePopup = false;

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

<div class="content">
  <Donator user={donation.donator} />
  <div>sent <Amount amount={donation.amount}/> to</div>
  <YoutubeChannel channel={donation.youtube_channel} logo/>
  {#if donation.lightning_address}
    <div>using ⚡{donation.lightning_address}</div>
  {/if}
  {#if donation.youtube_video}
    <div>for the video</div>
    <iframe
      width="560"
      height="315"
      src="https://www.youtube-nocookie.com/embed/{donation.youtube_video.video_id}"
      title="YouTube video player"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
    ></iframe>
  {/if}
  <Button on:click={() => showSharePopup = true}>Share</Button>
</div>
<ModalPopup bind:show={showSharePopup}>
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
  <Button on:click={copyAndShare}>Copy and Share</Button>
</ModalPopup>

<style>
.content {
  display: flex;
  gap: 16px;
  flex-direction: column;
  align-items: center;

  font-weight: 900;
  font-size: 24px;
}
</style>
