<script>
  import { navigate } from "svelte-navigator";
  import Loader from "$lib/Loader.svelte"
  import { clickDispatcher } from "$lib/utils.js";

  export let disabled = false;
  export let link = null;
  export let target = null;

  let spin = false;

  // This dispatcher returns promise
  function createAwaitableDispatcher() {
    const component = get_current_component();

    return (type, detail) => {
      const callbacks = component.$$.callbacks[type];

      if (callbacks) {
        // TODO are there situations where events could be dispatched
        // in a server (non-DOM) environment?
        const arr = [];
        const hasCallbacks = !!callbacks.length;
        const event = custom_event(type, detail);
        callbacks.slice().forEach(fn => {
          const res = fn.call(component, event);
          if (res instanceof Promise) {
            arr.push(res);
          }
        });
        return Promise.all(arr).then(() => hasCallbacks);
      }
      return new Promise((resolve) => resolve(false));
    };
  }

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

<button on:click={click} disabled={disabled || spin}>
  {#if spin}
    <div class="loader">
      <Loader />
    </div>
  {:else}
    <slot />
  {/if}
</button>

<style>
button {
  font-weight: var(--font-weight, 700);
  font-size: var(--font-size, inherit);
  color: var(--text-color, var(--link-color));
  padding: var(--padding, 12px 0);
  cursor: pointer;
  height: var(--height, auto);
  width: var(--width, 100%);
  transition: all 0.2s ease;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;

  border-width: var(--border-width, 2px);
  border-style: solid;
  border-color: var(--border-color);
  border-radius: 50px;
  background-image: var(--background-image);
  background-color: var(--button-background-color);
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
</style>
