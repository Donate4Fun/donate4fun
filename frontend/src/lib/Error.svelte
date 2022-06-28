<script>
  export let message;
</script>

{#if message}
<span {...$$restProps}>{message}</span>
{/if}

<style>
span {
  color: #FF4B4B;
  font-size: 12px;
}
</style>
