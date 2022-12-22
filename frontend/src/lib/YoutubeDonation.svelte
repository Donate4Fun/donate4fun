<script>
  import { link } from "svelte-navigator";

  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import Editable from "$lib/Editable.svelte";
  import Button from "$lib/Button.svelte";
  import WhiteButton from "$lib/WhiteButton.svelte";
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
  <div class="main">
    <div class="image-name">
      <img alt="avatar" class="avatar" src={donation.donator.avatar_url}>
      <div class="name">{donation.donator.name}</div>
    </div>
    <div class="amount blue">sent <b>{donation.amount} sats</b> to</div>
    <a use:link href="/youtube/{donation.youtube_channel.id}" class="youtube-channel">
      <div class="image-name">
        <img alt="avatar" class="avatar" src={donation.youtube_channel.thumbnail_url}>
        <div class="name">{donation.youtube_channel.title}</div>
        {#if donation.lightning_address}
          <span class="lightning-address">via ⚡{donation.lightning_address}</span>
        {/if}
      </div>
      {#if donation.youtube_channel.handle}
        <div class="handle">
          <span>{donation.youtube_channel.handle}</span>
        </div>
      {/if}
    </a>
  </div>
  {#if donation.cancelled_at === null && donation.claimed_at === null}
    <div class="buttons">
      <WhiteButton on:click={() => showSharePopup = true}>Share</WhiteButton>
      <WhiteButton link="/youtube/{donation.youtube_channel.id}/owner">Claim</WhiteButton>
    </div>
  {/if}
  {#if donation.youtube_video}
    <div class="for-the-video">for the video</div>
    <iframe
      class="video"
      src="https://www.youtube-nocookie.com/embed/{donation.youtube_video.video_id}"
      title="YouTube video player"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen
    ></iframe>
  {/if}
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

  font-weight: 900;
  font-size: 24px;
}
.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #2E6CFF;
  width: 100%;
}
.youtube-channel {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: Montserrat;
  color: inherit;
}
.image-name {
  display: flex;
  gap: 12px;
}
img.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  --filter: drop-shadow(4px 4px 20px rgba(34, 60, 103, 0.15)) drop-shadow(10px 15px 25px rgba(209, 217, 230, 0.4));
  border: 2px solid #FFFFFF;
  box-shadow: 4px 4px 20px rgba(34, 60, 103, 0.15), 10px 15px 25px rgba(209, 217, 230, 0.4);
}
.name {
  color: inherit;
  font-weight: 900;
  font-size: 24px;
  line-height: 29px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.handle {
  display: flex;
  gap: 8px;

  font-weight: 500;
  font-size: 12px;
  line-height: 15px;
  padding-left: 44px;
}
.lightning-address {
  color: var(--color);
}
.amount {
  padding-left: 44px;
  font-weight: 400;
  font-size: 24px;
  line-height: 29px;
  color: inherit;
}
.amount b {
  color: #19B400;
  font-weight: 800;
}
.buttons {
  display: flex;
  align-items: center;
  flex-direction: row;
  gap: 16px;
  width: 100%;
  height: 40px;
  --height: 100%;
  --font-size: 16px;
}
.video {
  aspect-ratio: 16 / 9;
  width: 100%;
}
@media (max-width: 640px) {
  .name,.amount {
    font-size: 20px;
    line-height: 24px;
  }
}
.for-the-video {
  font-weight: 400;
  font-size: 16px;
}
</style>
