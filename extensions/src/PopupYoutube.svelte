<script>
  import { useNavigate } from "svelte-navigator";
  import PopupSection from "./PopupSection.svelte";
  import {  worker, connectToPage, browser, subscribe } from "./common.js";
  import cLog from "./log.js";
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
    try {
      contentScript = await connectToPage();
    } catch (error) {
      cLog("couldn't connect to content script", error);
      return;
    }
    videoId = await contentScript.getVideoId();
    channelTitle = await contentScript.getChannelTitle();
    channelLogo = await contentScript.getChannelLogo();
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
 
<PopupSection --justify-content=space-between>
  {#await load() then}
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
      <div class="flex-grow">
        <Input type=number bind:value={amount} min={amountMin} max={amountMax} suffix=sats required />
      </div>
      <FiatAmount bind:amount={amount} class="fiat-amount min-width-70" />
    </div>
    <Button --width=100% on:click={donate}>Donate</Button>
  {/await}
</PopupSection>
