<script>
  import { useNavigate } from "svelte-navigator";

  import cLog from "$lib/log.js";
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import AmountSelection from "$lib/AmountSelection.svelte";
  import { worker, connectToPage, browser } from "$extlib/common.js";
  import PopupSection from "$extlib/PopupSection.svelte";

  let tweetUrl;
  let authorName;
  let authorAvatar;
  let contentScript;

  const navigate = useNavigate();

  async function load() {
    contentScript = await connectToPage();
    if (!contentScript)
      return;
    if (await contentScript.isTweetPage()) {
      ({ tweetUrl, authorName, authorAvatar } = await contentScript.getTweetInfo());
    }
  }

  async function donate(amount) {
    try {
      contentScript.onPaid(await contentScript.donate(amount, tweetUrl));
    } catch (err) {
      console.error("Failed to donate", err);
      const rejected = err.message === 'User rejected';
      navigate(`/nowebln/${amount}/${rejected}`);
    }
  }
</script>
 
<PopupSection>
  {#await load() then}
    {#if !tweetUrl}
      <div class="empty">
        <NumberedItem number=1>
          <span>Open a tweet or author you want to donate to</span>
        </NumberedItem>
        <NumberedItem number=2>
          <span>Click a ⚡ icon under the tweet or use this popup</span>
        </NumberedItem>
      </div>
    {:else}
      <div class="filled">
        <div class="filled-header">
          <img src="./static/twitter.svg" height=16 alt="twitter logo">
          <div class="donate-to">
            Donate to
            <span class="channel-title ellipsis">{authorName}</span>
          </div>
          {#if authorAvatar}
            <img width=44 height=44 class="circular" src={authorAvatar} alt="avatar">
          {/if}
        </div>
        <AmountSelection donate={donate} />
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
  white-space: nowrap;
  min-width: 0;
  gap: 0.5em;
  font-weight: 400;
}
.channel-title {
  font-weight: 800;
}
</style>
