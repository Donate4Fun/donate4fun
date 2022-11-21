<script>
  import Button from "$lib/Button.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Loader from "$lib/Loader.svelte";
  import { notify } from "$lib/notifications.js";
  import { sleep } from "$lib/utils.js";
  import { get, ApiError } from "$lib/api.js";

  let i = 0;
  let resolve;
</script>

<Spinner />
<Loader />
<div>
  <Button on:click={() => {notify(`default title ${i}`, 'default message', 'error', 15000); i++;}}>notify</Button>
  <Button on:click={() => {return new Promise((resolve_) => {resolve = resolve_;})}}>Start Loader</Button>
  <Button on:click={() => {resolve && resolve();}}>Stop Loader</Button>
  <Button on:click={() => {throw new Error("some error");}}>Throw error</Button>
  <Button on:click={async () => {throw new ApiError({data: {error: "some error data"}});}}>Throw ApiError</Button>
  <Button on:click={async () => { get("nonexistent"); }}>Fetch API - 400</Button>
</div>

<style>
div {
  width: 253px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
