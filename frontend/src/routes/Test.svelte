<script>
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import {notify} from '../lib/notifications.js';
  console.log(notify);

  let i = 0;
</script>

<Spinner />
<div><Button on:click={() => {notify(`default title ${i}`, 'default message'); i++;}}>button</Button></div>

<style>
div {
  align-self: start;
}
</style>
