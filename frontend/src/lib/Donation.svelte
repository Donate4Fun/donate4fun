<script>
  import { onMount, onDestroy } from 'svelte';
  import { link, useNavigate } from "svelte-navigator";

  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import Loading from "$lib/Loading.svelte";
  import Amount from "$lib/Amount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Editable from "$lib/Editable.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import Donator from "$lib/Donator.svelte";
  import TwitterDonation from "$lib/TwitterDonation.svelte";
  import { me } from "$lib/session.js";
  import { copy, youtube_video_url, youtube_channel_url } from "$lib/utils.js";
  import api from "$lib/api.js";

  export let donation;
  let navigate = useNavigate();
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

  async function cancel() {
    await api.post(`donation/${donation.id}/cancel`);
  }

  let ws;
  onDestroy(async () => {
    await ws?.close();
  });

  async function subscribe() {
    ws = api.subscribe(`donation:${donation.id}`, { autoReconnect: false });
    ws.on("notification", async (notification) => {
      await ws.close();
      ws = null;
      donation = (await api.get(`donation/${donation.id}`)).donation;
    });
    await ws.ready();
  }

  onMount(subscribe);
</script>

<main>
  {#if donation.paid_at}
    <div class="cancelled-container" class:cancelled={donation.cancelled_at !== null}>
      {#if donation.youtube_channel}
        <ChannelLogo url={donation.youtube_channel.thumbnail_url} size=72px />
        <div class="header">
          <p>Great! You've sent <Amount amount={donation.amount}/> to</p>
          <YoutubeChannel channel={donation.youtube_channel}/>
        </div>
        {#await $me then me}
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
            <Button on:click={() => navigate(-1)} class="grey">Back</Button>
          {/if}
        {/await}
      {:else if donation.twitter_account}
        <TwitterDonation {donation} />
      {/if}
    </div>
    {#if donation.cancelled_at}
      <div class="status-message">
        Donation cancelled
      </div>
    {:else if donation.claimed_at}
      <div class="status-message">
        Donation claimed
      </div>
    {:else}
      {#await $me then me}
        {#if donation.donator.id === me.donator.id}
          <Button
            --background-image="linear-gradient(white,white)"
            --border-width=0
            --text-color="#FF4B4B"
            --shadow="none"
            on:click={cancel}
          >Cancel donation</Button>
        {/if}
      {/await}
    {/if}
  {:else}
    Unpaid donation
  {/if}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding: 58px;
  width: 640px;
}
.cancelled-container {
  width: 100%;
}
.cancelled {
  opacity: 0.5;
}
.header {
  display: flex;
  flex-direction: column;
  align-items: center;

  font-weight: 900;
  font-size: 24px;
}
.status-message {
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
}
</style>
