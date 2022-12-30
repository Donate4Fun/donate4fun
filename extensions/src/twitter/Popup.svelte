<script>
  import { useNavigate } from "svelte-navigator";

  import cLog from "$lib/log.js";
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import AmountSelection from "$lib/AmountSelection.svelte";
  import SocialUserpic from "$lib/SocialUserpic.svelte";

  import { worker, connectToPage, browser } from "$extlib/common.js";
  import PopupSection from "$extlib/PopupSection.svelte";

  let pageUrl;
  let authorName;
  let authorAvatar;
  let authorHandle;
  let contentScript;

  const navigate = useNavigate();

  async function load() {
    contentScript = await connectToPage();
    if (!contentScript)
      return;
    if (await contentScript.isTweetPage()) {
      ({ pageUrl, authorName, authorHandle, authorAvatar } = await contentScript.getTweetInfo());
    } else if (await contentScript.isAuthorPage()) {
      ({ pageUrl, authorName, authorHandle, authorAvatar } = await contentScript.getAuthorInfo());
    }
  }

  async function donate(amount) {
    try {
      const donatorHandle = await contentScript.getCurrentAccountHandle();
      await contentScript.donate(amount, pageUrl, donatorHandle);
    } catch (err) {
      console.error("Failed to donate", err);
      const rejected = err.message === 'User rejected';
      navigate(`/nowebln/${amount}/${rejected}`);
    }
  }
</script>
 
<PopupSection>
  {#await load() then}
    {#if !pageUrl}
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
          {#if authorAvatar}
            <SocialUserpic social="twitter" src={authorAvatar} />
          {:else}
            <img src="/static/twitter.svg" alt="twitter" width=44 height=44>
          {/if}
          <div class="donate-to">
            <span class="author-name ellipsis">{@html authorName}</span>
            <span class="author-handle">@{authorHandle}</span>
          </div>
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
  align-items: center;
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
  gap: 10px;
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
.author-name {
  font-weight: 800;
  display: flex;
  gap: 4px;
}
.author-name :global(img) {
  width: 1em;
}
.author-handle {
  opacity: 0.9;
  font-size: 14px;
}
</style>
