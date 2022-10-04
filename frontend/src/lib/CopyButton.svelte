<script>
  import Button from "$lib/Button.svelte";
  import { copy } from "$lib/utils.js";

  export let content;
  let copied = false;

  async function doCopy() {
    copy(content);
    copied = true;
    setTimeout(() => copied = false, 3000);
  }
</script>

<Button on:click={doCopy}>
  {#if copied}
  Copied
  {:else}
  Copy
  {/if}
</Button>
