<script>
  import BaseButton from "$lib/BaseButton.svelte";
  import { clickDispatcher } from "$lib/utils.js";

  export let link;
</script>

<div>
  <BaseButton on:click={clickDispatcher()} {link} target="_blank" {...$$restProps}>
    <slot />
  </BaseButton>
</div>

<style>
div {
  display: contents;
  --border-color: rgba(46, 108, 255, 0.2);
}
div:hover:enabled {
  --shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
}
</style>
