<script>
  import { clickDispatcher } from "$lib/utils.js";
  import BaseButton from "$lib/BaseButton.svelte";
</script>

<div class=outer>
  <BaseButton
    --padding="var(--inner-border-width, 2px)"
    --background-image="linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%)"
    --border-width=0
    on:click={clickDispatcher()}
    {...$$restProps}
  >
    <div class=inner>
      <slot />
    </div>
  </BaseButton>
</div>

<style>
.outer {
  display: contents;
  --inner-background-image: var(--background-image);
  --inner-padding: var(--padding, 12px 0);
  --inner-border-width: var(--border-width);
}
.outer:hover {
  --shadow: 0px 8px 20px rgba(185, 192, 204, 0.4);
}
.inner {
  width: 100%;
  height: 100%;
  background: white;
  /* 2px less that in BaseButton */
  border-radius: 48px;
  padding: var(--inner-padding);
  background-image: var(--inner-background-image);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
