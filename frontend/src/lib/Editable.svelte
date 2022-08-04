<script>
  export let message;
  export let editable = true;

  function setEditable(node) {
    node.contentEditable = editable;
  }
</script>

<div contenteditable translate=no use:setEditable bind:innerHTML={message} {...$$restProps}>
</div>

<style>
div {
  border-radius: 8px;
  background-color: #F8F8F8;
  border-width: 1px;
  border-style: solid;
  padding: 1em;
  border-color: #7000FF;
}
</style>
