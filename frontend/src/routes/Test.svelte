<script>
  import Page from "../lib/Page.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import {notify} from '../lib/notifications.js';
  console.log(notify);

  let i = 0;
</script>

<Page>
  <Spinner />
  <div><Button on:click={() => {notify(`default title ${i}`, 'default message'); i++;}}>button</Button></div>
</Page>

<style>
div {
  align-self: start;
}
</style>
