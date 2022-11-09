<script>
	import { createEventDispatcher, onMount } from 'svelte';
  import Button from "$lib/Button.svelte";
  import Arrow2 from "$extlib/Arrow2.svelte";
  import { getStatic } from "$extlib/common.js";
  import { isCommentEnabled } from "./youtube.js";

  export let element = null;
  export let amount;

	const dispatch = createEventDispatcher();

  let textElement;
  let invert = 0;
  onMount(() => {
    if (isCommentEnabled()) {
      const color = window.getComputedStyle(textElement).getPropertyValue("color");
      invert = color === "rgb(255, 255, 255)" ? 100 : 0;
    }
    hideOnClickOutside(element);
  });

  function hideOnClickOutside(element) {
    if (!element)
      cInfo("hideOnClickOutside element is null", element);
    const outsideClickListener = event => {
      if (!element.contains(event.target)) {
        document.removeEventListener('mousedown', outsideClickListener);
        dispatch('click-outside');
      }
    }
    document.addEventListener('mousedown', outsideClickListener);
  }
</script>

<div bind:this={element} class="comment">
  <div class="flex-row inner-comment justify-center">
    <div class="flex-column gap-3">
      <p class="text-align-center margin-0 nowrap">Donated ⚡{amount} sats</p>
      {#if isCommentEnabled()}
        <button class="flex-row align-center button" on:click={() => dispatch("comment")}  >
          <span bind:this={textElement}>Post a comment</span>
          <div class="arrow" style="filter: invert({invert}%)">
            <Arrow2 />
          </div>
        </button>
      {/if}
    </div>
  </div>
</div>

<style>
.comment {
  position: absolute;
  top: 120%; /* place under the bolt vertically */
  left: -80px; /* center horizontally under the bolt button */
  font-size: 12px;
  /* simulate new round YouTube style */
  border-radius: 12px;
  background-color: var(--yt-spec-menu-background);
  box-shadow: 0px 4px 32px 0px var(--yt-spec-static-overlay-background-light);

  animation: moveit 900ms ease forwards;
  z-index: var(--ytd-z-index-toggle-button-tooltip);
  opacity: 1;
}
.inner-comment {
  padding: 7px 28px 8px 28px;
  gap: 9px;
  background-color: var(--yt-spec-badge-chip-background);
  color: var(--yt-spec-text-primary);
  border-radius: inherit;
}
button {
  border: 0;
  gap: 10px;
  background-color: var(--yt-spec-call-to-action);
  color: var(--yt-spec-text-primary-inverse);
  border-radius: 18px;
  font-size: var(--ytd-tab-system-font-size);
  font-weight: var(--ytd-tab-system-font-weight);
  font-family: inherit;
  padding: var(--yt-button-padding-minus-border);
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
