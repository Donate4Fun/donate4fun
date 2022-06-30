<script>
  import Button from "../lib/Button.svelte";
  import { copy } from "../lib/utils.js";

  export let lnurl;
  let copied = false;

  function doCopy() {
    copy(lnurl);
    copied = true;
  }
</script>

<div {...$$restProps}>
  <span>{lnurl}</span>
  <Button on:click={doCopy}>
  {#if copied}
  Copied
  {:else}
  Copy
  {/if}
  </Button>
</div>

<style>
div {
  display: flex;
  align-items: center;
  background-color: #F8F8F8;
  border-color: #E7E7E7;
  border-radius: 100px;
  border-width: 1px;
  border-style: solid;
  box-sizing: border-box;
  padding-left: 24px;
}
div span {
  overflow: hidden;
  font-size: 12px;
  line-height: 1em;
  text-overflow: clip;
}
div :global(button) {
  align-self: end;
}
</style>
