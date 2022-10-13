<script>
  import { useNavigate } from "svelte-navigator";
  import PopupSection from "./PopupSection.svelte";
  import { worker, connectToPage, browser } from "./common.js";
  import cLog from "$lib/log.js";
  import Button from "$lib/Button.svelte";
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";

  let videoId;
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
    videoId = await contentScript.getVideoId();
    cLog("videoid", videoId);
    if (videoId) {
      channelTitle = await contentScript.getChannelTitle();
      channelLogo = await contentScript.getChannelLogo();
    }
  }

  async function donate() {
    try {
      contentScript.onPaid(await contentScript.donate(amount, `https://youtube.com/watch?v=${videoId}`));
    } catch (err) {
      console.error("Failed to donate", err);
      if (err.message === "No webln found")
        navigate(`/nowebln/${amount}`);
    }
  }

  function toText(amount) {
    return amount >= 1000 ? `${amount / 1000} K` : amount;
  }
</script>
 
<PopupSection>
  <div class="main">
    {#await load() then}
      {#if !videoId}
        Navigate to video or channel..
      {:else}
        <div class="flex-row align-center justify-center gap-8 width-full">
          <img src="./static/youtube.svg" height=24px alt="youtube logo">
          <span class="flex-shrink-0 font-weight-900 font-20 line-height-24">Donate to</span>
          <div class="flex-shrink-1 flex-row align-center gap-16 grid-span-2">
            <img width=48px height=48px class="circular" src={channelLogo} alt="channel logo">
            <span class="color-blue font-weight-700">{channelTitle}</span>
          </div>
        </div>
        <div class="flex-row justify-space-between width-full">
        {#each amounts as amount_}
          <Button on:click={() => amount = amount_} --width=120px selected={amount_ === amount}>{toText(amount_)} ⚡</Button>
        {/each}
        </div>
        <div class="flex-row gap-20 align-center width-full">
          <div class="flex-grow input">
            <Input type=number bind:value={amount} min={amountMin} max={amountMax} suffix=sats required />
          </div>
          <FiatAmount bind:amount={amount} class="min-width-70" />
        </div>
        <Button --width=100% on:click={donate}>Donate</Button>
      {/if}
    {/await}
  </div>
</PopupSection>

<style>
.input {
  font-weight: 400;
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.015em;
}
.main {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  height: 100%;

  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
  letter-spacing: 0.02em;
}
</style>
