<script>
  import BaseButton from "$lib/BaseButton.svelte";
  import { clickDispatcher } from "$lib/utils.js";

  export let selected = false;
</script>

<div class:selected>
  <BaseButton on:click={clickDispatcher()} {...$$restProps}>
    <slot />
  </BaseButton>
</div>

<style>
div {
  display: contents;
}
.selected {
  --border-width: 2px;
  --border-color: #FF8A00;
  --background-image: linear-gradient(90deg, rgba(249, 240, 62, 0.9) 0%, rgba(157, 237, 162, 0.9) 100%);
}
:not(.selected) {
  --border-width: 1px;
  --background-image: linear-gradient(90deg, rgba(249, 240, 62, 0.4) 0%, rgba(157, 237, 162, 0.4) 100%);
  --border-color: rgba(26, 41, 82, 0.05);
  --shadow: 10px 15px 25px rgba(209, 217, 230, 0.4);
}
</style>
