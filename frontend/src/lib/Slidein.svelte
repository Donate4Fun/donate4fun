<script>
  import { fade } from 'svelte/transition';
  import { inview } from 'svelte-inview';
  import ScrollMagic from 'scrollmagic';

  import { cLog } from "$lib/log.js";

  let elem;
  let animate = false;
  const controller = new ScrollMagic.Controller()

  onMount(() => {
    const scene = new ScrollMagic.Scene({
      triggerHook: 0.9
    })
  });

  function onChangeAnimate({detail}) {
    if (!animate) {
      cLog("no animation", elem);
      return;
    }
    const animation = elem.getAnimations()[0];
    if (detail.inView && detail.scrollDirection.vertical === 'up') {
      cLog("forward", elem);
      animation.playbackRate = 1;
      animation.play();
    }
    if (!detail.inView && detail.scrollDirection.vertical === 'down') {
      cLog("backward", elem);
      animation.playbackRate = -1;
      animation.play();
    }
  }

  function onChangeInit({detail}) {
    if (detail.inView && detail.scrollDirection.vertical === 'up') {
      cLog("add class", elem);
      animate = true;
    }
    if (!detail.inView && detail.scrollDirection.vertical === 'down') {
      cLog("remove class", elem);
      animate = false;
    }
  }
</script>

<div
  use:inview={{}}
  on:change={onChangeInit}
>
  <div
    use:inview={{rootMargin: '-100px'}}
    on:change={onChangeAnimate}
  >
    <div bind:this={elem} class:noanimate={!animate} class:animate>
      <slot />
    </div>
  </div>
</div>

<style>
.noanimate {
  animation: none;
}
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
  }
  100% {
    transform: translateY(0);
  }
}
</style>
