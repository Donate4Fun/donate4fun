<script>
  import CopyButton from "../lib/Button.svelte";

  export let lnurl;
</script>

<div {...$$restProps}>
  <span>{lnurl}</span>
  <CopyButton bind:content={lnurl} />
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
  text-overflow: ellipsis;
}
div :global(button) {
  align-self: end;
  font-size: 15px !important;
}
</style>
