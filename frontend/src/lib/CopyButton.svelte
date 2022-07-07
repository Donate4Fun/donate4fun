<script>
  import Button from "../lib/Button.svelte";
  import {copy, sleep} from "../lib/utils.js";

  export let content;
  let text = "Copy";

  async function doCopy() {
    copy(content);
    text = "Copied";
    await sleep(3000);
    text = "Copy";
  }
</script>
<Button on:click={doCopy}>{text}</Button>
<style>
</style>
