<script>
  import { onMount, onDestroy, tick } from "svelte";
  import { backIn, expoIn } from "svelte/easing";
  import { Confetti } from "svelte-confetti";

  import { subscribe, get } from "$lib/api.js";
  import { worker, pageScript, donate, getStatic } from "$extlib/common.js";
  import { cLog, cInfo } from "$lib/log.js";
  import Bolt from "$lib/Bolt.svelte";
  import { getVideoId, postComment, isShorts } from "./youtube.js";
  import CommentTip from "./CommentTip.svelte";
  import HoldAmountButton from "$lib/HoldAmountButton.svelte";

	export let text = '…';
  export let loading = true;

  let isCommentPosted = false;
  let videoWS;
  let confetti = false;
  let showCommentTip = false;
  let donation = {amount: null};
  let commentTipElement;
  let shorts = isShorts();
  let amount = 0;
  let donating;

  async function fetchStats() {
    const videoId = getVideoId();
    const videoInfo = await get(`youtube-video/${videoId}`);
    cLog("video info", videoInfo);
    text = videoInfo.total_donated;
    loading = false;
  }

  async function apiGet(path) {
    return await worker.fetch("get", path);
  }

  async function doDonate(event) {
    donating = true;
    amount = event.detail.amount || await worker.getConfig("amount");
    try {
      await donate(amount, window.location.href);
    } catch (err) {
      donating = false;
    }
  }

  export async function onPaid(donation_) {
    donating = false;
    confetti = false;
    await tick();
    confetti = true;
    if (await worker.getConfig("enableComment") && !isCommentPosted) {
      donation = donation_;
      showCommentTip = true;
    }
  }

  async function onCommentClick() {
    const videoLanguage = donation.youtube_video.default_audio_language;
    showCommentTip = false;
    // Return immediately to avoid button spinner
    postComment(videoLanguage, donation.amount).then(() => { isCommentPosted = true; });
  }

  async function init() {
    cLog("onMount");

    const videoId = getVideoId();
    videoWS = subscribe(`youtube-video-by-vid:${videoId}`, { autoReconnect: false });
    videoWS.on("notification", (notification) => {
      cLog("youtube video updated", notification);
      text = notification.total_donated;
    });
    try {
      await videoWS.ready();
    } catch (err) {
      cInfo("Failed to subscribe to video notifications", err);
      text = "";
      return;
    }
    await fetchStats();
  }

  onMount(init);
  onDestroy(async () => {
    cLog("onDestroy");
    await videoWS.close();
  });

	function popOut(node, { duration }) {
		return {
			duration,
			css: (t, u) => {
        if (donating) {
          const eased = expoIn(t);
          return `
            transform: scale(${eased});
          `;
        } else {
          const eased = backIn(u);
          return `
            transform: scale(${1 + eased});
            opacity: ${1 - eased};
          `;
        }
			}
		};
	}

  cLog("Created Bolt");
</script>

<div class="root" class:shorts class:full={!shorts}>
  <div class="button" disabled={donating}>
    <HoldAmountButton bind:amount={amount} on:release={doDonate}>
      {#if confetti}
        <Confetti />
      {/if}
      <button class="bolt-button">
        <div class="icon" class:animate={donating}>
          <Bolt />
        </div>
        <div class="text" class:loading>{text}</div>
      </button>
      {#if amount}
        <div class="tooltip" style:display=block out:popOut={{duration: 200}}>
          ⚡{amount.toFixed()} sats
        </div>
      {:else if !donating && !showCommentTip}
        <div class="tooltip tooltip-hover">
          Donate sats
        </div>
      {/if}
    </HoldAmountButton>
  </div>
  {#if showCommentTip}
    <CommentTip bind:element={commentTipElement} amount={donation.amount} on:comment={onCommentClick} on:click-outside={() => {showCommentTip = false;}} />
  {/if}
</div>

<style>
:global(ytd-menu-renderer[has-flexible-items]) {
  overflow-y: visible !important; /* show our absolutely positioned popups */
  width: 99.999% !important; /* trigger youtube action buttons recalculation (they use ResizeObserver)*/
}
:global(#donate4fun-button) {
  margin-right: 8px;
}
.root {
  position: relative;
  width: 100%;
  --yt-button-icon-padding: 6px;
}
.button {
  /* youtube round style */
  display: flex;
  align-items: center;
  padding: 0 16px;
  height: 36px;
  background-color: var(--yt-spec-badge-chip-background);
  border-radius: 18px;
  cursor: pointer;
}
.button:hover {
  background-color: var(--yt-spec-mono-tonal-hover);
  border-color: transparent;
}
.bolt-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-right: var(--yt-button-icon-padding,8px);
  color: inherit;
  border-width: 0;
  background-color: transparent;
  font-family: inherit;
  cursor: pointer;
}
.shorts .bolt-button {
  flex-direction: column;
  color: var(--yt-spec-text-secondary);
}
.full .bolt-button {
  flex-direction: row;
  color: var(--yt-spec-icon-inactive);
}
.icon {
  line-height: 1;
  color: var(--yt-button-color,inherit);
  background-color: transparent;
  text-transform: var(--yt-button-text-transform,inherit);
  display: inline-block;
  position: relative;
  box-sizing: border-box;
  font-size: 0;

  margin-left: -6px;
  margin-right: 6px;
}
.full .icon {
  width: 24px;
  height: 24px;
}
.shorts .icon {
  height: var(--iron-icon-height,24px);
  width: var(--iron-icon-width,24px);
}
.tooltip {
  text-transform: none;
  font-size: 1.2rem;
  line-height: 1.8rem;
  font-weight: 400;
  outline: none;
  -webkit-font-smoothing: antialiased;
  background-color: var(--paper-tooltip-background, #616161);
  color: var(--paper-tooltip-text-color, white);
 
  position: absolute;
  z-index: var(--ytd-z-index-toggle-button-tooltip);
  white-space: nowrap;

  display: none;
  margin: 8px;
  padding: 8px;
  border-radius: 4px;
}
.full .tooltip {
  top: calc(100% + 8px); /* try to mimic youtube popups */
}
.shorts .tooltip {
  right: calc(72px); /* try to mimic youtube popups */
}
.bolt-button:hover + .tooltip-hover {
  display: block;

  opacity: 0;
  animation-delay: var(--paper-tooltip-delay-in, 500ms);
  animation-name: keyFrameFadeInOpacity;
  animation-iteration-count: 1;
  animation-timing-function: ease-in;
  animation-duration: var(--paper-tooltip-duration-in, 500ms);
  animation-fill-mode: forwards;
}
@keyframes dff-glow {
  to {
    filter: drop-shadow(0px 0px 5px);
  }
}
.bolt-button:hover .icon {
  animation-name: dff-glow;
  animation-duration: 0.8s;
  animation-direction: alternate;
  animation-iteration-count: infinite;
  animation-timing-function: ease-out;
}
.text {
  /*color: var(--yt-button-icon-button-text-color,var(--yt-spec-text-secondary));*/
  font-size: var(--ytd-tab-system-font-size);
  font-weight: var(--ytd-tab-system-font-weight);
  letter-spacing: var(--ytd-tab-system-letter-spacing);
  text-transform: var(--ytd-tab-system-text-transform);
}
.loading {
  overflow: hidden;
  display: inline-block;
  vertical-align: bottom;
  animation: dff-ellipsis steps(3,end) 600ms infinite;
  --width: 0.6em;
}
@keyframes dff-ellipsis {
  from {
    margin-left: 0;
    margin-right: var(--width);
    width: 0;
  }
  50% {
    margin-left: 0;
    margin-right: 0;
    width: var(--width);
  }
  to {
    margin-left: var(--width);
    margin-right: 0;
    width: 0;
  }
}
.animate {
  animation: 600ms cubic-bezier(.7,.09,.93,.68) 0s infinite dff-beat !important;
}
@keyframes dff-beat {
  to {
    transform: scale(2);
    opacity: 0%;
  }
}
@keyframes dff-amount-hide {
  0% {
    animation-timing-function: ease-out;
    transform: scale(1);
  }
  50% {
    transform: scale(0.8);
  }
  100% {
    transform: scale(3);
    opacity: 0.1;
  }
}
</style>
