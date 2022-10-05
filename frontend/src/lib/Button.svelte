<script>
  import { navigate } from "svelte-navigator";
  import { custom_event, get_current_component } from 'svelte/internal'
  import Spinner from "$lib/Spinner.svelte";

  export let link = null;
  export let target = null;
  export let spin = false;
  export let selected = false;
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

<button {...$$restProps} on:click={click} disabled={disabled || spin} class:selected>
  <div class="flex-row align-center">
    {#if spin}
      <div class="spinner"></div>
    {:else}
      <slot />
    {/if}
  </div>
</button>

<style>
button {
  background-image: var(--background-image, linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%));
  font-weight: var(--font-weight, 700);
  font-size: var(--font-size, 16px);
  color: black;
  padding: var(--padding, 12px 25px);
  cursor: pointer;
  height: var(--height, auto);
  width: var(--width, 100%);

  border: 0;
  border-radius: 100px;

  /* identical to box height, or 150% */
  letter-spacing: 0.02em;
}
button div {
  justify-content: center;
  height: 100%;
  width: 100%;
}
/* border */
button.white,button.light {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  padding: 2px;
}
button.blue {
  background: rgba(46, 108, 255, 0.2);
  padding: 2px;
}
button.white div,button.light div, button.blue div {
  border-radius: inherit;
  padding: var(--padding, 10px 23px);  /* parent padding - 2px (pseudo-border) */
}
/* background */
button.white div,button.blue div {
  background: white;
}
button.light div {
  background: linear-gradient(105.38deg, rgba(249, 240, 62, 0.2) 1.16%, rgba(157, 237, 162, 0.2) 95.37%), #FFFFFF;
}
button.grey {
  background: #E9E9E9;
}
button:disabled {
  opacity: 0.5;
}
button:hover:enabled {
  box-shadow: 0px 8px 20px rgba(185, 192, 204, 0.6);
}
.selected {
  border: 2px solid #FF8A00;
}
.spinner::after {
  display: inline-block;
  animation: dotty steps(1,end) 1s infinite;
  content: '';
}
@keyframes dotty {
  0%   { content: ''; }
  25%  { content: '.'; }
  50%  { content: '..'; }
  75%  { content: '...'; }
  100% { content: ''; }
}
</style>
