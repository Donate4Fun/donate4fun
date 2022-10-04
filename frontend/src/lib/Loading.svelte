<script>
  import Spinner from "../lib/Spinner.svelte";
</script>
<div>
  <Spinner --size=5em --width=1em />
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
