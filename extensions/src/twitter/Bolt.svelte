<script>
  import { tick } from "svelte";
  import { quintOut } from "svelte/easing";
  import { slide, fade } from 'svelte/transition';
  import { LottiePlayer } from '@lottiefiles/svelte-lottie-player';

  import Bolt from "$lib/Bolt.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import Button from "$lib/Button.svelte";
  import { cLog, cInfo } from "$lib/log.js";
  import { worker, donate, getStatic, waitElement, pageScript, selectByPattern } from "$extlib/common.js";
  import { getCurrentAccountHandle } from "./twitter.js";

  export let tweetUrl;
  let donating = false;
  let amount = 0;
  let confetti = false;
  let elem;
  let lottiePlayer;
  const amountItems = [{value: 100, text: '100'}, {value: 1000, text: '1K'}, {value: 10_000, text: '10K'}];
  let holdButton;

  async function doDonate() {
    donating = true;
    const amount_ = amount || await worker.getConfig('amount');
    amount = 0;
    try {
      await donate(amount_, tweetUrl, getCurrentAccountHandle());
    } catch (err) {
      donating = false;
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
      if (await worker.getConfig("enableReply")) {
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

  function fixAmount(amount_) {
    holdButton.pause();
    amount = amount_;
  }

  function resumeIncrease() {
    holdButton.resume();
  }

  function whoosh(node, params) {
    const existingTransform = getComputedStyle(node).transform.replace('none', '');

    return {
      delay: params.delay || 0,
      duration: params.duration || 400,
      easing: params.easing || elasticOut,
      css: (t, u) => `transform: ${existingTransform} scale(${t}) translateY(calc(${u} * 35px))`
    };
  }
</script>

<div bind:this={elem} class="container">
  {#if confetti}
    <div class="animating-bolt">
      <LottiePlayer
        src={getStatic("lottie-bolt.json")}
        autoplay={true}
        loop={false}
        width={34}
        height={39}
        background=transparent
        controls={null}
        controlsLayout={[]}
        bind:this={lottiePlayer}
      />
    </div>
  {:else if donating}
    <div class="donating-bolt"><Bolt /></div>
  {:else}
    <HoldButton bind:this={holdButton} bind:amount={amount} on:release={doDonate}>
      {#if amount}
        <div class="amount-container">
          ⚡ <span class="amount">{amount.toFixed()}</span> sats
        </div>
        <div class="select-tooltip" in:whoosh="{{delay: 250, duration: 300, easing: quintOut }}">
          {#each amountItems as amount_}
            <div
              on:mouseenter={() => fixAmount(amount_.value)}
              on:mouseleave={resumeIncrease}
              on:mouseup={doDonate}
            >
              <Button
                --padding="8px"
                selected={amount_.value === amount}
                dimmed={amount_.value !== amount}
              >⚡{amount_.text}</Button>
            </div>
          {/each}
        </div>
      {:else}
        <div class="bolt-circle">
          <div class="bolt">
            <Bolt />
          </div>
        </div>
        <div class="tooltip">
          Hold to donate more
        </div>
      {/if}
    </HoldButton>
  {/if}
</div>

<style>
.container {
  position: relative;
  display: flex;
  align-self: center;
  justify-content: center;
  margin: -10px 0;
  align-items: center;
  color: rgb(83, 100, 113);
  cursor: pointer;
  font-family: "TwitterChirp";
  min-width: 34px;
  min-height: 39px;
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
  min-width: 120px;
  user-select: none;
}
.bolt-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  outline-style: none;
  width: calc(1.25em + 16px);
  height: calc(1.25em + 16px);
}
.animating-bolt {
}
.donating-bolt {
  width: 10px;
}
@media (prefers-color-scheme: dark) {
  .container {
    color: rgb(113, 118, 123);
  }
  .amount {
    color: rgb(231, 233, 234);
  }
  .tooltip {
    background-color: rgba(91, 112, 131, 0.8);
  }
}
@media (prefers-color-scheme: light) {
  .tooltip {
    background-color: rgba(0, 0, 0, 0.6);
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
.tooltip {
  position: absolute;
  display: none;
  top: -20px;
  left: -35px;
  padding: 2px 4px;
  border-radius: 2px;

  font-size: 11px;
  line-height: 12px;
  font-weight: 400;
  color: white;
  font-family: TwitterChirp, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;

  white-space: nowrap;
  opacity: 0;
}
.bolt-circle:hover + .tooltip {
  display: block;

  opacity: 1;
  transition-property: opacity;
  transition-delay: 500ms;
  transition-duration: 500ms;
}
.select-tooltip {
  position: absolute;
  display: flex;
  align-items: center;
  top: -35px;
  left: -30px;
  display: flex;
  gap: 4px;
}
</style>
