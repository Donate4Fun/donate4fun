<script>
  import Button from "../lib/Button.svelte";
  import {copy, sleep} from "../lib/utils.js";

  export let content;
  let copied = false;

  async function doCopy() {
    copy(content);
    copied = true;
    await sleep(3000);
    copied = false;
  }
</script>

<Button on:click={doCopy} nospin>
  {#if copied}
  Copied
  {:else}
  Copy
  {/if}
</Button>
