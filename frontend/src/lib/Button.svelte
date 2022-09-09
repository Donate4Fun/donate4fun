<script>
  import { navigate } from "svelte-navigator";
  import { custom_event, get_current_component } from 'svelte/internal'
  import Spinner from "../lib/Spinner.svelte";

  export let link = null;
  export let target = null;
  export let spin = false;
  export let nospin = false;
  export let selected = false;

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
    } else {
      if (!nospin)
        spin = true;
      try {
        await dispatch("click", ev);
      } catch (err) {
      }
      spin = false;
    }
  }
</script>

<button {...$$restProps} on:click={click} disabled={spin} class:selected>
  <div class="flex-row align-center">
    {#if spin}
      <Spinner class="spinner" size=20px width=3px />
    {/if}
    <slot />
  </div>
</button>

<style>
button {
  background-image: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
  color: black;
  padding: 5px 20px;
  cursor: pointer;
  height: 40px;

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
button.white {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  padding: 2px;
}
button.white div {
  background: white;
  border-radius: inherit;
  padding: 5px 20px;
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
.spinner {
  left: -30px;
}
.selected {
  border: 2px solid #FF8A00;
}
</style>
