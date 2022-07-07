<script>
  export let message;
</script>

<div contenteditable class="message" bind:innerHTML={message} {...$$restProps}>
</div>

<style>
.message {
  border-radius: 8px;
  background-color: #F8F8F8;
  border-width: 1px;
  border-style: solid;
  padding: 1em;
  border-color: #7000FF;
}
</style>
