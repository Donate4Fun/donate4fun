<script>
  import Loader from "$lib/Loader.svelte";
</script>
<div>
  <Loader --size=5em />
  <h1>Loading...</h1>
</div>

<style>
div {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1em;
}
</style>
