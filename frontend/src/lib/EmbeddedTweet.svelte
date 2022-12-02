<script>
  import { onMount } from "svelte";

  export let id;
  let element;

  onMount(async () => {
    await twttr.widgets.createTweet(id.toString(), element);
  });
</script>

<div bind:this={element}></div>

<style>
div {
  width: 100%;
}
</style>
