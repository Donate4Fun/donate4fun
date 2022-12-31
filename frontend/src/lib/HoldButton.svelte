<script>
  import { createEventDispatcher } from "svelte";
  import { slide } from 'svelte/transition';

  import BaseButton from "$lib/BaseButton.svelte";
  import { clickDispatcher } from "$lib/utils.js";

  let holding = false;
  let holded = false;
  let spin = false;
  let showTooltip = false;
  const dispatchClick = clickDispatcher();

  function onMouseDown() {
    holding = true;
    holded = false;
    showTooltip = false;
  }

  function onMouseUp() {
    if (holded)
      click();
    else
      showTooltip = true;
    holding = false;
    holded = false;
  }

  function onMouseLeave() {
    holding = false;
    holded = false;
  }

  function onAnimationEnd(ev) {
    if (holding)
      holded = true;
  }

  async function click() {
    spin = true;
    try {
      await dispatchClick();
    } finally {
      spin = false;
    }
  }
</script>

<BaseButton
  --padding=0
  --height=40px
  spin={spin}
>
  <div
    class="main"
    class:holding={holding}
    class:holded={holded}
    on:mousedown={onMouseDown}
    on:mouseup={onMouseUp}
    on:mouseleave={onMouseLeave}
    on:animationend|self={onAnimationEnd}
  >
    <div class="tooltip" class:show={showTooltip} on:animationend={() => showTooltip = false}>
      Hold this button
    </div>
    <slot />
  </div>
</BaseButton>

<style>
.main {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 100px;
  background-color: var(--background-color);
  border-width: var(--border-width);
  box-shadow: 0 0 0px var(--fill-color);
}
.tooltip {
  display: none;
  position: absolute;
  padding: 10px;
  border-radius: 5px;
  font-size: 14px;
  color: white;
  background: grey;
}
.tooltip.show {
  display: block;
  animation-name: tooltip;
  animation-duration: 3s;
  animation-timing-function: ease-in-out;
}
@keyframes tooltip {
  0% {
    opacity: 0%;
    top: 0;
  }
  5% {
    opacity: 10%;
  }
  10% {
    opacity: 100%;
    top: -40px;
  }
  90% {
    opacity: 100%;
    top: -40px;
  }
  95% {
    opacity: 10%;
  }
  100% {
    opacity: 0%;
    top: 0;
  }
}
.main.holding {
  animation-name: holding;
  animation-duration: 2s;
  animation-fill-mode: forwards;
  background-image: linear-gradient(to right, var(--fill-color) 50%, transparent 50%);
  background-size: 200%;
}
@keyframes holding {
  0% {
    background-position: right;
  }
  100% {
    background-position: left;
  }
}
.main.holded {
  animation-name: holded;
  animation-duration: 200ms;
  animation-fill-mode: forwards;
}
@keyframes holded {
  0% {
    box-shadow: 0 0 0px var(--fill-color);
  }
  90% {
    box-shadow: 0 0 15px var(--fill-color);
  }
  100% {
    box-shadow: 0 0 10px var(--fill-color);
  }
}
</style>
