<script>
  import Button from "../../frontend/src/lib/Button.svelte";
  import Arrow2 from "./Arrow2.svelte";
	import {createEventDispatcher} from 'svelte';
  import {getStatic} from "./common.js";

  export let element;
  export let amount;

	const dispatch = createEventDispatcher();
</script>

<div bind:this={element} class="comment">
  <div class="flex-row inner-comment">
    <div class="flex-column gap-3">
      <p class="text-align-center margin-0">Donated ⚡{amount} sats</p>
      <button class="flex-row align-center button" on:click={() => dispatch("comment")}  >
          <span>Post a comment</span>
          <div class="arrow">
            <Arrow2 />
          </div>
      </button>
    </div>
  </div>
</div>

<style>
.comment {
  padding: 1px;
  position: absolute;
  top: 100%; /* place under the bolt vertically */
  left: -80px; /* center horizontally under the bolt button */
  font-size: 12px;
  /*background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  border-radius: 8px;*/
  background-color: var(--yt-spec-brand-background-primary);
  animation: moveit 900ms ease forwards;
  z-index: var(--ytd-z-index-toggle-button-tooltip);
  opacity: 1;
  display: var(--dff-display, none);
  border: 1px solid var(--yt-spec-call-to-action);
}
.inner-comment {
  padding: 7px 28px 8px 28px;
  gap: 9px;
  background-color: var(--yt-spec-badge-chip-background);
  color: var(--yt-spec-text-primary);
  /*border-radius: 7px;*/
}
button {
  border: 0;
  gap: 10px;
  /*width: 161px;
  font-size: 12px;
  padding-left: 15px;
  height: 24px;
  padding: 0;*/
  background-color: var(--yt-spec-call-to-action);
  color: var(--yt-spec-text-primary-inverse);
  border-radius: var(--yt-button-border-radius,3px);
  font-size: var(--ytd-tab-system-font-size);
  font-weight: var(--ytd-tab-system-font-weight);
  letter-spacing: var(--ytd-tab-system-letter-spacing);
  padding: var(--yt-button-padding,0.7em 0.57em);
  user-select: none;
  cursor: pointer;
}
button span {
  text-align: center;
  white-space: nowrap;
}
button .arrow {
  margin: -10px;
}
@keyframes moveit {
  0% { transform: translateY(-60px) scale3d(0.96,0.96,1); }
  20% { transform: translateY(20px) scale3d(1.1,1.1,1); }
  40% { transform: translateY(-10px) scale3d(0.98,0.98,1); }
  60% { transform: translateY(2px) scale3d(1.05,1.05,1); }
  80% { transform: translateY(0px) scale3d(1.01,1.01,1); }
  100% { transform: translateY(0px) scale3d(1,1,1); }
}
</style>
