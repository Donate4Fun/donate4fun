<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { subscribe, get } from "$lib/api.js";
  import { Confetti } from "svelte-confetti";
  import { worker, pageScript, donate } from "./common.js";
  import { cLog, cInfo } from "$lib/log.js";
  import { getVideoId, postComment, isShorts } from "./youtube.js";
  import CommentTip from "./CommentTip.svelte";

	export let text = '…';
  export let animate = false;
  export let loading = true;

  let isCommentPosted = false;
  let videoWS;
  let confetti = false;
  let showCommentTip = false;
  let donation = {amount: null};
  let commentTipElement;
  let shorts = isShorts();

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

  async function doDonate(amount) {
    animate = true;
    let donation_;
    try {
      donation_ = await donate(amount, window.location.href);
    } catch (err) {
      animate = false;
      cInfo("Payment failed", err);
      const rejected = err.message === 'User rejected';
      worker.createPopup(`nowebln/${amount}/${rejected}`);
      return;
    }
    onPaid(donation_);
  }

  export async function onPaid(donation_) {
    animate = false;
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

  let holdAmount;
  let holdInterval;
  let showConfirmation = false;

  function onMouseDown() {
    holdAmount = 0;
    holdInterval = setInterval(() => {
      holdAmount += 10;
    }, 100);
  }

  async function onMouseUp() {
    clearInterval(holdInterval);
    const amount = holdAmount || await worker.getConfig("amount");
    holdAmount = 0;
    doDonate(amount);
  }

  cLog("Created Bolt");
</script>

<div class="root" class:shorts class:full={!shorts}>
  <div class="button">
    {#if confetti}
      <Confetti />
    {/if}
    <button class="bolt-button" on:mousedown={onMouseDown} on:mouseup={onMouseUp} disabled={animate}>
      <div class="icon" class:animate>
        <svg viewBox="60 60 160 160" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path class="bolt" d="M79.7609 144.047L173.761 63.0466C177.857 60.4235 181.761 63.0466 179.261 67.5466L149.261 126.547H202.761C202.761 126.547 211.261 126.547 202.761 133.547L110.261 215.047C103.761 220.547 99.261 217.547 103.761 209.047L132.761 151.547H79.7609C79.7609 151.547 71.2609 151.547 79.7609 144.047Z" stroke-width="10"></path>
          </g>
        </svg>
      </div>
      <div class="text" class:loading>{text}</div>
    </button>
    <div class="tooltip tooltip-hover" style:visibility={holdAmount ? 'hidden' : 'visible'} style-target="tooltip">
      Donate sats
    </div>
    <div class="tooltip" style:display={holdAmount ? 'block' : 'none'} style-target="tooltip">
      ⚡{holdAmount} sat
    </div>
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
.root {
  position: relative;
  width: 100%;
  --yt-button-icon-padding: 6px;
}
.button {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.bolt-button {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding-right: var(--yt-button-icon-padding,8px);
  color: inherit;
  border-width: 0;
  background-color: transparent;
  font-family: inherit;
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
  padding: var(--yt-button-icon-padding,8px);
  color: var(--yt-button-color,inherit);
  background-color: transparent;
  text-transform: var(--yt-button-text-transform,inherit);
  display: inline-block;
  position: relative;
  box-sizing: border-box;
  font-size: 0;
}
.full .icon {
  width: var(--yt-button-icon-size,var(--yt-icon-width,40px));
  height: var(--yt-button-icon-size,var(--yt-icon-height,40px));
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
  display: block;
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
  border-radius: 2px;
}
.full .tooltip {
  top: calc(100% + 4px); /* try to mimic youtube popups */
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
.bolt {
  fill: var(--iron-icon-fill-color,currentcolor);
  stroke: var(--iron-icon-stroke-color,none);
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
</style>
