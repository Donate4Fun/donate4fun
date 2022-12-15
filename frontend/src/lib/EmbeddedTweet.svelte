<script>
  import { tick } from "svelte";
  import Loader from "$lib/Loader.svelte";

  export let id;
  let element;

  async function loadTweet() {
    await tick();
    console.log("elem", element);
    await twttr.widgets.createTweet(id.toString(), element);
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
