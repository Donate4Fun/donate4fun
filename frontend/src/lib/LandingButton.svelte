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
  --border-color: #2E6CFF;
  --color: #2E6CFF;
  --border-width: 4px;
  --shadow: 0px 10px 40px rgba(46, 108, 255, 0.2);
  --background-image: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
}
div:hover {
  --shadow: 0px 10px 40px rgba(46, 108, 255, 0.4);
}
</style>
