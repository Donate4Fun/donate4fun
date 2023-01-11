<script>
  import { clickDispatcher } from "$lib/utils.js";
  import BaseButton from "$lib/BaseButton.svelte";
  import ColoredBorder from "$lib/ColoredBorder.svelte";

  export let height = 'auto';
</script>

<BaseButton
  --height={height}
  --inner-padding="var(--padding)"
  --border-width=0
  --inner-background-image=var(--background-image)
  on:click={clickDispatcher()}
  padding=0
  {...$$restProps}
>
  <ColoredBorder>
    <div class="inner">
      <slot />
    </div>
  </ColoredBorder>
</BaseButton>

<style>
.inner {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: inherit;
  padding: var(--padding);
  background-image: var(--inner-background-image);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
