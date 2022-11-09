<script>
  import { tick } from "svelte";
  import { backIn, expoIn } from "svelte/easing";
  import { LottiePlayer } from '@lottiefiles/svelte-lottie-player';

  import Bolt from "$lib/Bolt.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import { cLog, cInfo } from "$lib/log.js";
  import { worker, donate, getStatic } from "./common.js";

  export let tweetUrl;
  let donating = false;
  let amount = 0;
  let confetti = false;
  let hasReply = false;
  let elem;

  async function doDonate(event) {
    donating = true;
    amount = event.detail.amount || await worker.getConfig('amount');
    try {
      const donation = await donate(amount, tweetUrl);
      donating = false;
      onPaid(donation);
    } catch (err) {
      donating = false;
      cInfo("Payment failed", err);
      const rejected = err.message === 'User rejected';
      worker.createPopup(`nowebln/${amount}/${rejected}`);
    }
  }

  export async function onPaid(donation_) {
    donating = false;
    confetti = false;
    await tick();
    confetti = true;
    if (await worker.getConfig("enableComment") && !hasReply) {
      postReply(donation_);
    }
  }

  function postReply() {
    const replyButton = elem.parentElement.parentElement.querySelector('[data-testid="reply"]');
    replyButton.click();
    cLog("posting comment", language, amount);
    let comment;
    try {
      comment = await worker.getConfig(`defaultComment_${language}`);
    } catch (exc) {
      comment = await worker.getConfig("defaultComment");
    }
    comment.replace('%amount%', amount);
    document.activeElement.textContent = comment;
    await pageScript.emulateKeypresses(":focus");
  }
</script>

<div bind:this={elem} class="container">
  {#if confetti}
    <LottiePlayer
      src={getStatic("lottie-bolt.json")}
      autoplay={true}
      loop={false}
      width={30}
      background=transparent
      controls={null}
      controlsLayout={[]}
      height={null}
    />
  {:else}
    <HoldButton bind:amount={amount} on:release={doDonate}>
      {#if amount}
        <div class="amount-container">
          ⚡ <span class="amount">{amount.toFixed()}</span> sats
        </div>
      {:else}
        <div class="bolt-circle">
          <div class="bolt">
            <Bolt />
          </div>
        </div>
      {/if}
    </HoldButton>
  {/if}
</div>

<style>
.container {
  height: 100%;
  display: flex;
  align-items: center;
  color: rgb(83, 100, 113);
  cursor: pointer;
  font-family: "TwitterChirp";
}
.amount {
  font-weight: 700;
  color: rgb(231, 233, 234);
}
.amount-container {
  height: calc(1.25em + 16px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.2em;
}
.bolt-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  outline-style: none;
  width: calc(1.25em + 16px);
  height: calc(1.25em + 16px);
}
@media (prefers-color-scheme: dark) {
  .container {
    color: rgb(113, 118, 123);
  }
}
.bolt-circle:hover {
  background-color: rgba(240, 118, 29, 0.1);
  border-radius: 100%;
  transition-duration: 0.2s;
  transition-property: background-color, box-shadow;
  color: rgb(240, 128, 29);
}
.bolt {
  width: 1.25em;
  height: 1.25em;
}
</style>
