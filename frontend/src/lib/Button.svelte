<script>
  import { navigate } from "svelte-navigator";
  import { custom_event, get_current_component } from 'svelte/internal'
  import Loader from "$lib/Loader.svelte"

  export let link = null;
  export let target = null;
  export let spin = false;
  export let selected = false;
  export let dimmed = false;
  export let disabled = false;

  function createEventDispatcher() {
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

  const dispatch = createEventDispatcher();

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
      await dispatch("click", ev);
    } catch (err) {
      console.log("error in button on:click dispatcher", err);
    }
    spin = false;
  }
</script>

<div class="root">
  <button {...$$restProps} on:click={click} disabled={disabled || spin} class:selected class:dimmed>
    <div class="flex-row align-center">
      {#if spin}
        <div class="loader">
          <Loader />
        </div>
      {:else}
        <slot />
      {/if}
    </div>
  </button>
</div>

<style>
.root {
  display: contents;
  --border-width-secondary: var(--border-width, 2px);
  --border-width-primary: var(--border-width, 4px);
}
button {
  background-image: var(--background-image, linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%));
  font-weight: var(--font-weight, 700);
  font-size: var(--font-size, inherit);
  color: var(--link-color);
  padding: var(--padding, 12px 25px);
  cursor: pointer;
  height: var(--height, auto);
  width: var(--width, 100%);
  transition: all 0.2s ease;
  box-shadow: 0px 10px 40px rgba(46, 108, 255, 0.2), 10px 15px 20px rgba(209, 217, 230, 0.15);

  border: var(--border-width-primary) solid var(--link-color);
  border-radius: 100px;
  letter-spacing: 0.02em;
}
button div {
  justify-content: center;
  height: 100%;
  width: 100%;
}
button.white,button.light,button.blue,button.grey {
  border: 0;
  box-shadow: none;
}
/* border */
button.white,button.light {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  padding: var(--border-width-secondary);
}
button.blue {
  background: rgba(46, 108, 255, 0.2);
  padding: var(--border-width-secondary);
}
button.grey {
  background: #E9E9E9;
}
button.white > div,button.light > div, button.blue > div {
  border-radius: inherit;
  padding: var(--padding, 10px 23px);  /* parent padding - 2px (pseudo-border) */
}
button.selected {
  border: var(--border-width-secondary) solid #FF8A00;
  box-shadow: none;
}
button.dimmed {
  box-shadow: 10px 15px 25px rgba(209, 217, 230, 0.4);
  background: linear-gradient(90deg, rgba(249, 240, 62, 0.4) 0%, rgba(157, 237, 162, 0.4) 100%), #FFFFFF;
  border: 1px solid rgba(26, 41, 82, 0.05);
}
/* background */
button.white > div,button.blue > div {
  background: white;
}
button.light > div {
  background: linear-gradient(105.38deg, rgba(249, 240, 62, 0.2) 1.16%, rgba(157, 237, 162, 0.2) 95.37%), #FFFFFF;
}
button:disabled {
  opacity: 0.5;
}
button:hover:enabled {
  box-shadow: 0px 8px 20px rgba(185, 192, 204, 0.6);
}
.loader {
  display: flex;
  align-items: center;
  height: 1.219em; /* try to emulate 1lh (line-height) unit */
}
</style>
