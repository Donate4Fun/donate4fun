<script>
  import Button from "$lib/Button.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import {notify} from '$lib/notifications.js';

  let i = 0;
</script>

<Spinner />
<div><Button on:click={() => {notify(`default title ${i}`, 'default message', 'error', 15000); i++;}}>button</Button></div>

<style>
div {
  align-self: start;
}
</style>
