<script>
  import { fade } from 'svelte/transition';
  import { inview } from 'svelte-inview';

  import { cLog } from "$lib/log.js";

  let elem;

  function onChange({detail}) {
    const animation = elem.getAnimations()[0];
    if (detail.inView && detail.scrollDirection.vertical === 'up') {
      cLog("up start")
      animation.playbackRate = 1;
      animation.play();
    }
    if (!detail.inView && detail.scrollDirection.vertical === 'down') {
      cLog("down start");
      animation.playbackRate = -1;
      animation.play();
    }
  }
  function onEnter() {
    cLog("enter");
  }
</script>

<div
  class="wrapper"
  use:inview={{rootMargin: '-100px'}}
  on:change={onChange}
  on:enter={onEnter}
>
  <div bind:this={elem} class="animate">
    <slot />
  </div>
</div>

<style>
.animate {
	animation-name: slide-in-bottom;
  animation-duration: 0.3s;
  animation-direction: normal;
  animation-timing-function: cubic-bezier(0.250, 0.460, 0.450, 0.940);
  animation-fill-mode: both;
  animation-play-state: paused;
}
@keyframes slide-in-bottom {
  0% {
    transform: translateY(300px);
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>

