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
  --background-image: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
  --border-width: 0;
  --padding: 12px 20px;
}
div:hover {
  --shadow: 0px 8px 20px rgba(185, 192, 204, 0.6);
}
</style>
