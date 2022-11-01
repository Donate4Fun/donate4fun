<script>
  import Button from "$lib/Button.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Loader from "$lib/Loader.svelte";
  import {notify} from "$lib/notifications.js";
  import {sleep} from "$lib/utils.js";

  let i = 0;
  let resolve;
</script>

<Spinner />
<Loader />
<div>
  <Button on:click={() => {notify(`default title ${i}`, 'default message', 'error', 15000); i++;}}>notify</Button>
  <Button on:click={() => {return new Promise((resolve_) => {resolve = resolve_;})}}>Start Loader</Button>
  <Button on:click={() => {resolve && resolve();}}>Stop Loader</Button>
</div>

<style>
div {
  width: 253px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
