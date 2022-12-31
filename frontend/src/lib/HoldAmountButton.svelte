<script>
  import { createEventDispatcher } from "svelte";

  export let amount;

  let interval;
  let startTimer;
  const dispatch = createEventDispatcher();

  function onMouseDown() {
    startTimer = setTimeout(() => {
      amount = 100;
      resume();
    }, 100);
  }

  function onMouseUp() {
    if (interval) {
      dispatch('release', { amount: Math.round(amount) });
      amount = 0;
    } else if (startTimer) {
      dispatch('release', 0);
    }
    stopInterval();
  }

  function onMouseLeave() {
    stopInterval();
    amount = 0;
  }

  function stopInterval() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
    if (startTimer) {
      clearTimeout(startTimer);
      startTimer = null;
    }
  }

  export function pause() {
    stopInterval();
  }

  export function resume() {
    interval = setInterval(() => {
      amount = amount * 1.1;
    }, 100);
  }
</script>

<div on:mousedown={onMouseDown} on:mouseup={onMouseUp} on:mouseleave={onMouseLeave}>
  <slot />
</div>
