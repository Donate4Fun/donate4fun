<script>
  import { useNavigate } from "svelte-navigator";

  import PopupSection from "$extlib/PopupSection.svelte";
  import cLog from "$lib/log.js";
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import AmountSelection from "$lib/AmountSelection.svelte";
  import SocialUserpic from "$lib/SocialUserpic.svelte";
  import { me } from "$lib/session.js";
  import { youtube_video_url, youtubeChannelUrlByHandle } from "$lib/utils.js";
  import { worker, connectToPage, browser } from "$extlib/common.js";

  let videoId;
  let channelTitle;
  let channelLogo;
  let contentScript;
  let channelHandle;

  const navigate = useNavigate();

  async function load() {
    cLog("load youtube", window.location.hash);
    contentScript = await connectToPage();
    if (!contentScript)
      return;
    if (await contentScript.isVideoPage()) {
      videoId = await contentScript.getVideoId();
      cLog("videoid", videoId);
    }
    ({ channelTitle, channelHandle, channelLogo } = await contentScript.getChannelInfo());
  }

  async function donate(amount) {
    try {
      const target = videoId ? youtube_video_url(videoId) : youtubeChannelUrlByHandle(channelHandle);
      await contentScript.donate(amount, target);
    } catch (err) {
      console.error("Failed to donate", err);
    }
  }
</script>
 
<PopupSection>
  {#await load() then}
    {#if !videoId && !channelHandle}
      <div class="empty">
        <NumberedItem number=1>
          <span>Open video channel or author you want to donate to</span>
        </NumberedItem>
        <NumberedItem number=2>
          <span>Click a ⚡ icon under video or use this popup</span>
        </NumberedItem>
      </div>
    {:else}
      <div class="filled">
        <div class="filled-header">
          {#if channelLogo}
            <SocialUserpic social="youtube" src={channelLogo} />
          {:else}
            <img src="/static/twitter.svg" alt="twitter" width=44 height=44>
          {/if}
          <div class="donate-to">
            <span class="channel-title ellipsis">{channelTitle}</span>
            <span class="handle">@{channelHandle}</span>
          </div>
        </div>
        <div class="amount">
          <AmountSelection donate={donate} />
        </div>
      </div>
    {/if}
  {/await}
</PopupSection>

<style>
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
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  line-height: 22px;
}
.donate-to {
  display: flex;
  flex-direction: column;
  white-space: nowrap;
  min-width: 0;
  font-weight: 400;
}
.channel-title {
  font-weight: 800;
}
.amount {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.handle {
  color: rgb(96, 96, 96);
  font-size: 14px;
}
</style>
