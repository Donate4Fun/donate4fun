<script>
  import { tick } from "svelte";
  import { quintOut, elasticOut } from "svelte/easing";
  import { slide, fade } from 'svelte/transition';
  import { LottiePlayer } from '@lottiefiles/svelte-lottie-player';

  import Bolt from "$lib/Bolt.svelte";
  import HoldAmountButton from "$lib/HoldAmountButton.svelte";
  import AmountButton from "$lib/AmountButton.svelte";
  import { cLog, cInfo } from "$lib/log.js";
  import { worker, donate, getStatic, waitElement, pageScript, selectByPattern } from "$extlib/common.js";
  import { getCurrentAccountHandle } from "./twitter.js";

  export let pageUrl;
  export let isTweet;

  let donating = false;
  let amount = 0;
  let confetti = false;
  let elem;
  let lottiePlayer;
  const amountItems = [{value: 100, text: '100'}, {value: 1000, text: '1K'}, {value: 10_000, text: '10K'}];
  let holdButton;

  export function showPopup() {
    cLog("show popup");
    amount = 1;
  }

  async function doDonate() {
    donating = true;
    const amount_ = amount || await worker.getConfig('amount');
    amount = 0;
    try {
      await donate(amount_, pageUrl, getCurrentAccountHandle(), onPaid);
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
    const replyButton = isTweet
      ? elem.parentElement.parentElement.querySelector('[data-testid="reply"]')
      : document.querySelector('[data-testid="SideNav_NewTweet_Button"]');
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
    selectByPattern(textElement, /^.+!/g);
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
      css: (t, u) => `transform: ${existingTransform} scale(${t}) translateY(calc(${u} * 34px))`
    };
  }
</script>

<div bind:this={elem} class="container" class:container-author={!isTweet} class:container-tweet={isTweet}>
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
    <HoldAmountButton bind:this={holdButton} bind:amount={amount} on:release={doDonate}>
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
              <AmountButton
                --padding="8px"
                --background-opacity=1
                selected={amount_.value === amount}
              >⚡{amount_.text}</AmountButton>
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
    </HoldAmountButton>
  {/if}
</div>

<style>
.container {
  position: relative;
  display: flex;
  align-self: center;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  font-family: "TwitterChirp";
}
.container-tweet {
  min-width: 34px;
  min-height: 39px;
  color: rgb(83, 100, 113);
  margin: -10px 0;
}
.container-author {
  margin-right: 8px;
  margin-bottom: 12px;
  height: 36px;
  min-width: 36px;
  box-sizing: border-box;
  border-width: 1px;
  border-style: solid;
  border-radius: 1000px;
  border-color: rgb(207, 217, 222);
  color: rgb(15, 20, 25);
}
.container-author .select-tooltip {
  top: -36px;
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
  animation-name: shake;
  animation-duration: 100ms;
  animation-iteration-count: infinite;
}
@media (prefers-color-scheme: dark) {
  .container-tweet {
    color: rgb(113, 118, 123);
  }
  .container-author {
    color: rgb(239, 243, 244);
    border-color: rgb(83, 100, 113);
  }
  .amount {
    color: rgb(231, 233, 234);
  }
  .tooltip {
    background-color: rgba(0, 0, 0, 0.6);
  }
  .select-tooltip {
    color: rgb(15, 20, 25);
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
  background-color: rgba(91, 112, 131, 0.8);
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
  top: -34px;
  left: -30px;
  display: flex;
  gap: 4px;
  user-select: none;
  z-index: 1;
}
@keyframes shake {
  2% {
    transform: translate(-0.5px, 2.5px) rotate(-0.5deg); }
  4% {
    transform: translate(0.5px, -1.5px) rotate(-0.5deg); }
  6% {
    transform: translate(1.5px, -1.5px) rotate(1.5deg); }
  8% {
    transform: translate(0.5px, 2.5px) rotate(-0.5deg); }
  10% {
    transform: translate(-1.5px, 2.5px) rotate(1.5deg); }
  12% {
    transform: translate(2.5px, -0.5px) rotate(-0.5deg); }
  14% {
    transform: translate(2.5px, 2.5px) rotate(1.5deg); }
  16% {
    transform: translate(1.5px, 1.5px) rotate(0.5deg); }
  18% {
    transform: translate(0.5px, 2.5px) rotate(1.5deg); }
  20% {
    transform: translate(1.5px, -1.5px) rotate(-0.5deg); }
  22% {
    transform: translate(0.5px, 1.5px) rotate(1.5deg); }
  24% {
    transform: translate(-0.5px, 1.5px) rotate(0.5deg); }
  26% {
    transform: translate(-1.5px, -1.5px) rotate(0.5deg); }
  28% {
    transform: translate(1.5px, 2.5px) rotate(1.5deg); }
  30% {
    transform: translate(2.5px, -1.5px) rotate(1.5deg); }
  32% {
    transform: translate(1.5px, 1.5px) rotate(1.5deg); }
  34% {
    transform: translate(2.5px, 0.5px) rotate(-0.5deg); }
  36% {
    transform: translate(2.5px, -0.5px) rotate(-0.5deg); }
  38% {
    transform: translate(0.5px, 0.5px) rotate(0.5deg); }
  40% {
    transform: translate(1.5px, -1.5px) rotate(1.5deg); }
  42% {
    transform: translate(0.5px, -0.5px) rotate(0.5deg); }
  44% {
    transform: translate(-0.5px, -0.5px) rotate(-0.5deg); }
  46% {
    transform: translate(1.5px, 2.5px) rotate(-0.5deg); }
  48% {
    transform: translate(2.5px, 2.5px) rotate(1.5deg); }
  50% {
    transform: translate(0.5px, 2.5px) rotate(1.5deg); }
  52% {
    transform: translate(1.5px, -1.5px) rotate(1.5deg); }
  54% {
    transform: translate(0.5px, 0.5px) rotate(1.5deg); }
  56% {
    transform: translate(1.5px, 1.5px) rotate(0.5deg); }
  58% {
    transform: translate(0.5px, 0.5px) rotate(1.5deg); }
  60% {
    transform: translate(-0.5px, 0.5px) rotate(-0.5deg); }
  62% {
    transform: translate(2.5px, -1.5px) rotate(1.5deg); }
  64% {
    transform: translate(2.5px, -0.5px) rotate(0.5deg); }
  66% {
    transform: translate(0.5px, 0.5px) rotate(1.5deg); }
  68% {
    transform: translate(-1.5px, -0.5px) rotate(0.5deg); }
  70% {
    transform: translate(2.5px, 0.5px) rotate(-0.5deg); }
  72% {
    transform: translate(1.5px, 0.5px) rotate(1.5deg); }
  74% {
    transform: translate(0.5px, 0.5px) rotate(1.5deg); }
  76% {
    transform: translate(-1.5px, -0.5px) rotate(0.5deg); }
  78% {
    transform: translate(-1.5px, -1.5px) rotate(-0.5deg); }
  80% {
    transform: translate(-0.5px, -0.5px) rotate(0.5deg); }
  82% {
    transform: translate(-0.5px, 1.5px) rotate(1.5deg); }
  84% {
    transform: translate(-1.5px, 2.5px) rotate(-0.5deg); }
  86% {
    transform: translate(-1.5px, -0.5px) rotate(-0.5deg); }
  88% {
    transform: translate(2.5px, -0.5px) rotate(-0.5deg); }
  90% {
    transform: translate(2.5px, -1.5px) rotate(-0.5deg); }
  92% {
    transform: translate(2.5px, 0.5px) rotate(-0.5deg); }
  94% {
    transform: translate(0.5px, 1.5px) rotate(-0.5deg); }
  96% {
    transform: translate(1.5px, 2.5px) rotate(0.5deg); }
  98% {
    transform: translate(2.5px, -0.5px) rotate(1.5deg); }
  0%, 100% {
    transform: translate(0, 0) rotate(0); } }
</style>
