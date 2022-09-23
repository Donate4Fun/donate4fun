<script>
  import {onMount, onDestroy, tick} from 'svelte';
  import {Confetti} from "svelte-confetti";
  import {worker, subscribe, pageScript, cLog, sleep, donate} from "./common.js";
  import {getVideoId, postComment} from "./youtube.js";
  import CommentTip from "./CommentTip.svelte";

	export let text = '…';
  export let animate = false;
  export let loading = true;

  let isCommentPosted = false;
  let unsubscribeVideoWS;
  let confetti = false;
  let showCommentTip = false;
  let donation = {amount: null};
  let commentTipElement;

  async function fetchStats() {
    const videoId = getVideoId();
    const videoInfo = await apiGet(`youtube-video/${videoId}`);
    cLog("video info", videoInfo);
    text = videoInfo.total_donated;
    loading = false;
  }

  async function apiGet(path) {
    return await worker.fetch("get", path);
  }

  async function onDonateClicked(evt) {
    animate = true;

    try {
      onPaid(await donate(await worker.getConfig("amount"), window.location.href));
    } catch (err) {
      animate = false;
      console.error("Payment failed", err);
      openPopup("nowebln");
    }
  }

  export async function onPaid(donation_) {
    animate = false;
    confetti = false;
    await tick();
    confetti = true;
    if (await worker.getConfig("enableComment") && !isCommentPosted) {
      donation = donation_;
      showCommentTip = true;
      await tick();
      hideOnClickOutside(commentTipElement);
    }
  }

  async function onCommentClick() {
    const videoLanguage = donation.youtube_video.default_audio_language;
    showCommentTip = false;
    postComment(videoLanguage, donation.amount).then(() => { isCommentPosted = true; });
  }

  function hideOnClickOutside(element) {
    const outsideClickListener = event => {
      if (!element.contains(event.target)) {
        document.removeEventListener('click', outsideClickListener);
        showCommentTip = false;
      }
    }
    document.addEventListener('click', outsideClickListener);
}

  async function init() {
    cLog("onMount");
    const videoId = getVideoId();
    unsubscribeVideoWS = await subscribe(`youtube-video-by-vid:${videoId}`, (msg) => {
      cLog("youtube video updated", msg);
      fetchStats();
    });
    await fetchStats();
  }

  onMount(init);
  onDestroy(() => {
    cLog("onDestroy");

    if (unsubscribeVideoWS) {
      unsubscribeVideoWS();
    }
  });
</script>

<div class="root" id="donate4fun-button">
  <div class="flex-column align-center">
    {#if confetti}
      <Confetti />
    {/if}
    <div class="flex-row align-center bolt-button" on:click={onDonateClicked}>
      <div class="icon" class:animate>
        <svg viewBox="60 60 160 160" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path class="bolt" d="M79.7609 144.047L173.761 63.0466C177.857 60.4235 181.761 63.0466 179.261 67.5466L149.261 126.547H202.761C202.761 126.547 211.261 126.547 202.761 133.547L110.261 215.047C103.761 220.547 99.261 217.547 103.761 209.047L132.761 151.547H79.7609C79.7609 151.547 71.2609 151.547 79.7609 144.047Z" stroke-width="10"></path>
          </g>
        </svg>
      </div>
      <div class="text" class:loading>{text}</div>
    </div>
    <div class="tooltip" style-target="tooltip">
      Donate sats
    </div>
  </div>
  {#if showCommentTip}
    <CommentTip bind:element={commentTipElement} amount={donation.amount} on:comment={onCommentClick} />
  {/if}
</div>

<style>
:global(ytd-menu-renderer[has-flexible-items]) {
  overflow-y: visible !important; /* show our absolutely positioned popups */
  width: 99.999% !important; /* trigger youtube action buttons recalculation (they use ResizeObserver)*/
}
.root {
  display: inline-block;
  position: relative;
  --yt-button-icon-padding: 6px;
  color: var(--yt-spec-icon-inactive);
}
.bolt-button {
  justify-content: center;
  cursor: pointer;
  padding-right: var(--yt-button-icon-padding,8px);
}
.icon {
  line-height: 1;
  padding: var(--yt-button-icon-padding,8px);
  width: var(--yt-button-icon-size,var(--yt-icon-width,40px));
  height: var(--yt-button-icon-size,var(--yt-icon-height,40px));
  color: var(--yt-button-color,inherit);
  background-color: transparent;
  text-transform: var(--yt-button-text-transform,inherit);
  display: inline-block;
  position: relative;
  box-sizing: border-box;
  font-size: 0;
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
  top: calc(100% + 4px); /* try to mimic youtube popups */
  white-space: nowrap;

  display: none;
  margin: 8px;
  padding: 8px;
  border-radius: 2px;
}
.bolt-button:hover + .tooltip {
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
  color: var(--yt-button-icon-button-text-color,var(--yt-spec-text-secondary));
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
