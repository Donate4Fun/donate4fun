<script>
  import BaseButton from "$lib/BaseButton.svelte";
  import { clickDispatcher } from "$lib/utils.js";
</script>

<div>
  <BaseButton on:click={clickDispatcher()} {...$$restProps}>
    <slot />
  </BaseButton>
</div>

<style>
div {
  display: contents;
  --button-background-color: #E9E9E9;
  --border-width: 0;
}
div:hover:enabled {
  --button-background-color: #D9D9D9;
  --hover-shadow: 0px 8px 20px rgba(185, 192, 204, 0.4);
}
</style>
