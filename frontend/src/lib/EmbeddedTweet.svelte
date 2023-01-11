<script>
  import { tick } from "svelte";
  import Loader from "$lib/Loader.svelte";
  import { cError } from "$lib/log.js";

  export let id;
  let element;

  async function loadTweet() {
    await tick();
    if (typeof(twttr) !== 'undefined')
      await twttr.widgets.createTweet(id.toString(), element);
    else
      cError("Could not embed tweet because twttr is undefined");
  }
</script>

<div bind:this={element}>
  {#await loadTweet()}
    <Loader />
  {:then}
    <div></div>
  {/await}
</div>

<style>
div {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}
</style>
