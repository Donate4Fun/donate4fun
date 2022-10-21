<script>
  import { useNavigate } from "svelte-navigator";
  import PopupSection from "./PopupSection.svelte";
  import { worker, connectToPage, browser } from "./common.js";
  import cLog from "$lib/log.js";
  import { me } from "$lib/session.js";
  import Button from "$lib/Button.svelte";
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import { toText, youtube_video_url, youtube_channel_url } from "$lib/utils.js";

  let videoId;
  let channelId;
  let channelTitle;
  let channelLogo;
  let contentScript;
  export let amount = 100;

  const amounts = [100, 1000, 10000];
  const amountMin = 10;
  const amountMax = 1000000;
  const navigate = useNavigate();

  async function load() {
    cLog("load youtube", window.location.hash);
    contentScript = await connectToPage();
    if (!contentScript)
      return;
    if (await contentScript.isVideoPage()) {
      videoId = await contentScript.getVideoId();
      cLog("videoid", videoId);
    } else if (await contentScript.isChannelPage()) {
      channelId = await contentScript.getChannelId();
      cLog("channelid", channelId);
    }
    channelTitle = await contentScript.getChannelTitle();
    channelLogo = await contentScript.getChannelLogo();
  }

  async function donate() {
    try {
      const target = videoId ? youtube_video_url(videoId) : youtube_channel_url(channelId);
      contentScript.onPaid(await contentScript.donate(amount, target));
    } catch (err) {
      console.error("Failed to donate", err);
      if (err.message === "No webln found")
        navigate(`/nowebln/${amount}`);
    }
  }
</script>
 
<PopupSection>
  {#await load() then}
    {#if !videoId && !channelId}
      <div class="empty">
        <NumberedItem number=1>
          <span>Open video channel or author you want to donate</span>
        </NumberedItem>
        <NumberedItem number=2>
          <span>Click a ⚡ icon under video or use this popup</span>
        </NumberedItem>
      </div>
    {:else}
      <div class="filled">
        <div class="filled-header">
          <img src="./static/youtube.svg" height=16 alt="youtube logo">
          <div>
            Donate to
            <span class="channel-title">{channelTitle}</span>
          </div>
          {#if channelLogo}
            <img width=44 height=44 class="circular" src={channelLogo} alt="channel logo">
          {/if}
        </div>
        <div class="amount">
          <div class="amount-buttons">
          {#each amounts as amount_}
            <Button
              on:click={() => amount = amount_}
              --padding="8px"
              selected={amount_ === amount}
              dimmed={amount_ !== amount}
            >{toText(amount_)} ⚡</Button>
          {/each}
          </div>
          <div class="amount-input">
            <div class="flex-grow input">
              <Input type=number bind:value={amount} min={amountMin} max={amountMax} suffix=sats required />
            </div>
            <FiatAmount bind:amount={amount} />
          </div>
        </div>
        {#await $me then me}
          {#if amount <= me.donator.balance}
            <Button --width=100% on:click={donate} --padding="9px">Donate</Button>
          {:else}
            <Button --width=100% on:click={donate} --padding="9px">Donate with WebLN</Button>
          {/if}
        {/await}
      </div>
    {/if}
  {/await}
</PopupSection>

<style>
.input {
  font-weight: 400;
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.015em;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 64px;

  font-size: 16px;
  line-height: 24px;
  letter-spacing: 0.02em;
}
.filled {
  display: flex;
  flex-direction: column;
  gap: 42px;
  width: 100%;
  height: 100%;

  font-weight: 700;
  font-size: 16px;
  line-height: 20px;
  letter-spacing: 0.02em;
}
.filled-header {
  display: flex;
  align-items: center;
  gap: 8px;

  font-size: 16px;
  line-height: 22px;
  font-weight: 800;
}
.channel-title {
  color: var(--link-color);
}
.amount {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.amount-buttons {
  display: flex;
  gap: 16px;

  font-size: 14px;
  line-height: 20px;
}
.amount-input {
  display: flex;
  align-items: center;
  gap: 20px;

  font-size: 14px;
  line-height: 24px;
}
</style>
