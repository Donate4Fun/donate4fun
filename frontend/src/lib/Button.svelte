<script>
  import { createEventDispatcher } from "svelte";
  import { navigate } from "svelte-navigator";

  export let link = null;

  const dispatch = createEventDispatcher();
  function click(ev) {
    console.log("click", ev, link);
    if (link !== null) {
      navigate(link);
    } else {
      dispatch("click", ev);
    }
  }
</script>

<button {...$$restProps} on:click={click}>
  <div>
    <slot />
  </div>
</button>

<style>
button {
  background: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
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
  display: flex;
  align-items: center;
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
</style>
