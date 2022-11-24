<script>
  import { tick } from "svelte";
  import { backIn, expoIn } from "svelte/easing";
  import { LottiePlayer } from '@lottiefiles/svelte-lottie-player';

  import Bolt from "$lib/Bolt.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import { cLog, cInfo } from "$lib/log.js";
  import { worker, donate, getStatic, waitElement, pageScript, selectByPattern } from "$extlib/common.js";
  import { getCurrentAccountHandle } from "./twitter.js";

  export let tweetUrl;
  let donating = false;
  let amount = 0;
  let confetti = false;
  let hasReply = false;
  let elem;
  let lottiePlayer;

  async function doDonate(event) {
    donating = true;
    amount = event.detail.amount || await worker.getConfig('amount');
    try {
      const donation = await donate(amount, tweetUrl, getCurrentAccountHandle());
      donating = false;
      onPaid(donation);
    } catch (err) {
      donating = false;
      cInfo("Payment failed", err);
      const rejected = err.message === 'User rejected';
      worker.createPopup(`nowebln/${amount}/${rejected}`);
    }
  }

  export async function onPaid(donation) {
    donating = false;
    confetti = false;
    await tick();
    confetti = true;
    await tick();
    const lottie = lottiePlayer.getLottie();
    lottie.addEventListener("complete", async () => {
      confetti = false;
      cLog("amount", donation.amount);
      if (await worker.getConfig("enableComment") && !hasReply) {
        await postReply(donation);
      }
    });
  }

  async function postReply(donation) {
    const apiHost = await worker.getConfig("apiHost");
    const replyButton = elem.parentElement.parentElement.querySelector('[data-testid="reply"]');
    replyButton.click();
    await waitElement('[contenteditable="true"]');
    cLog("posting comment", donation);
    let comment = await worker.getConfig("twitterDefaultReply");
    comment = comment.replace('%amount%', donation.amount);
    comment = comment.replace('%link%', `${apiHost}/donation/${donation.id}`);
    await pageScript.emulateKeypresses(":focus", comment);
    const textElement = document.activeElement.querySelector('[data-text="true"]');
    if (textElement === null)
      return;
    selectByPattern(textElement, /^.+!/g)
  }
</script>

<div bind:this={elem} class="container">
  {#if confetti}
    <LottiePlayer
      src={getStatic("lottie-bolt.json")}
      autoplay={true}
      loop={false}
      width={30}
      height={30}
      background=transparent
      controls={null}
      controlsLayout={[]}
      bind:this={lottiePlayer}
    />
  {:else if donating}
    <div>...</div>
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
  display: flex;
  align-self: center;
  margin: -10px 0;
  align-items: center;
  color: rgb(83, 100, 113);
  cursor: pointer;
  font-family: "TwitterChirp";
}
.amount {
  font-weight: 700;
  color: rgb(15, 20, 25);
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
  .amount {
    color: rgb(231, 233, 234);
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
