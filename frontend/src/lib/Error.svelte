<script>
  export let message;
</script>

{#if message}
<p>{message}</p>
{/if}

<style>
  p {
    font-color: red;
  }
</style>
