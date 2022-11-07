<script>
  import { createEventDispatcher } from "svelte";

  export let amount;

  let interval;
  const dispatch = createEventDispatcher();

  function onMouseDown() {
    amount = 10;
    interval = setInterval(() => {
      amount = amount * 1.1;
    }, 100);
  }

  function onMouseUp() {
    if (interval) {
      dispatch('release', { amount: Math.round(amount) });
      amount = 0;
    }
  }

  function onMouseLeave() {
    endHold();
    amount = 0;
  }

  function endHold() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  }
</script>

<div on:mousedown={onMouseDown} on:mouseup={onMouseUp} on:mouseleave={onMouseLeave}>
  <slot />
</div>
