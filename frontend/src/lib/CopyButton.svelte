<script>
  import WhiteButton from "$lib/WhiteButton.svelte";
  import { copy } from "$lib/utils.js";

  export let content;
  let copied = false;

  async function doCopy() {
    copy(content);
    copied = true;
    setTimeout(() => copied = false, 3000);
  }
</script>

<WhiteButton on:click={doCopy} {...$$restProps} --padding="12px 20px">
  {#if copied}
    Copied
  {:else}
    Copy
  {/if}
</WhiteButton>
