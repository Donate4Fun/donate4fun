<script>
  import { useNavigate } from "svelte-navigator";
  import {worker, contentScript, browser, subscribe, isTest} from "./common.js";
  import Button from "../../frontend/src/lib/Button.svelte";
  import Input from "../../frontend/src/lib/Input.svelte";
  import FiatAmount from "../../frontend/src/lib/FiatAmount.svelte";

  let videoId;
  let channelTitle;
  let channelLogo;
  export let amount = 100;

  const amounts = [100, 1000, 10000];
  const amountMin = 10;
  const amountMax = 1000000;
  const navigate = useNavigate();

  async function load() {
    console.log("load youtube", window.location.hash);
    if (isTest()) {
      videoId = 'JB2-DmUqtS8';
      channelTitle = 'Alby - Send and Receive Bitcoin on the Web';
      channelLogo = 'https://yt3.ggpht.com/1D4XwPDDBz5-6YYDp_bYryT5HOQao13w3pi32q9KlV12lpDqyg3NOc07-oKIiLQZpc_UUdl9hYo=s88-c-k-c0x00ffffff-no-rj'
    } else {
      videoId = await contentScript.getVideoId();
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
 
{#await load() then}
  <section class="flex-grow-1">
    <div class="flex-column align-center justify-space-between">
      <div class="grid grid-columns-3 width-full">
        <span class="font-weight-900 font-20 flex-row align-center">Donate to</span>
        <div class="flex-row align-center gap-16 grid-span-2">
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
    </div>
  </section>
{/await}

<style>
section {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  border-radius: 20px;
  padding: 2px;
  height: 100%;
}
section > div {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 20px;
  padding: 40px 32px 36px 32px;
}
</style>
