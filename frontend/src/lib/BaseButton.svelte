<script>
  import { navigate } from "svelte-navigator";
  import Loader from "$lib/Loader.svelte"
  import { clickDispatcher } from "$lib/utils.js";

  export let disabled = false;
  export let link = null;
  export let target = null;
  export let title = null;
  export let spin = false;
  export let padding = "12px 0";

  const dispatchClick = clickDispatcher();

  async function click(ev) {
    if (link !== null) {
      if (target !== null) {
        window.open(link, target).focus();
      } else {
        navigate(link);
      }
    }
    spin = true;
    try {
      await dispatchClick(ev);
    } finally {
      spin = false;
    }
  }
</script>

<button on:click={click} disabled={disabled || spin} title={title} style:padding={padding}>
  {#if spin}
    <div class="loader">
      <Loader />
    </div>
  {/if}
  <div class="wrapper" class:hidden={spin}>
    <slot />
  </div>
</button>

<style>
button {
  font-weight: var(--font-weight, 700);
  font-size: var(--font-size, inherit);
  color: var(--text-color, var(--link-color));
  cursor: pointer;
  height: var(--height, auto);
  width: var(--width, 100%);
  transition: all 0.2s ease;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  user-select: none;
  -webkit-tap-highlight-color: transparent;

  border-width: var(--border-width, 2px);
  border-style: solid;
  border-color: var(--border-color);
  border-radius: 50px;
  background-image: var(--background-image);
  background-color: var(--button-background-color);
  background-clip: padding-box;
  -webkit-background-clip: padding-box;
  letter-spacing: 0.02em;
}
button:hover:enabled {
  box-shadow: var(--shadow, 0px 8px 20px rgba(185, 192, 204, 0.6));
}
button:disabled {
  opacity: 0.5;
  box-shadow: none;
}
.loader {
  display: flex;
  align-items: center;
  height: 1.219em; /* try to emulate 1lh (line-height) unit */
}
.wrapper {
  display: contents;
}
.wrapper.hidden {
  display: none;
}
</style>
