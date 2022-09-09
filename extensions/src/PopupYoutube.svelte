<script>
  import {worker, contentScript, browser, subscribe, isTest} from "./common.js";
  import Button from "../../frontend/src/lib/Button.svelte";
  import Input from "../../frontend/src/lib/Input.svelte";
  import FiatAmount from "../../frontend/src/lib/FiatAmount.svelte";

  let videoId;
  let channelTitle;
  let channelLogo;
  let amount = 100;
  export let showWeblnMessage = false;

  const amounts = [100, 1000, 10000];
  const amountMin = 10;
  const amountMax = 1000000;

  async function load() {
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
    console.log("paying", amount);
    const response = await worker.fetch('post', 'donate', {
      amount: amount,
      target: `https://youtube.com/watch?v=${videoId}`,
    });
    if (response.payment_request) {
      console.log("Not enough balance, try to trigger webln payment");
      try {
        await new Promise(async (resolve, reject) => {
          let unsubscribeWs = await subscribe(`donation:${response.donation.id}`, async (msg) => {
            unsubscribeWs();
            resolve();
          });
          try {
            await contentScript.sendPayment(response.payment_request);
          } catch (err) {
            unsubscribeWs();
            reject(err);
          }
        });
      } catch (err) {
        console.error("Failed to donate using webln", err);
        showWeblnMessage = true;
        // TODO: open next page
        return;
      }
    }
    console.log("Successefuly donated");
    if (await worker.getConfig("enableComment")) {
      const videoLanguage = response.donation.youtube_video.default_audio_language;
      await contentScript.postComment(videoLanguage, amount);
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
      <div class="flex-row justify-center gap-16">
      {#each amounts as amount_}
        <Button on:click={() => amount = amount_} class="width-120" selected={amount_ === amount}>{toText(amount_)} ⚡</Button>
      {/each}
      </div>
      <div class="flex-row gap-20 align-center width-full">
        <div class="flex-grow">
          <Input type=number bind:value={amount} min={amountMin} max={amountMax} suffix=sats required />
        </div>
        <FiatAmount bind:amount={amount} class="fiat-amount min-width-70" />
      </div>
      <Button class="width-full" on:click={donate}>Donate</Button>
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
