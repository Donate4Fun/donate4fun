<script>
  export let message;
</script>

{#if message}
<p>{message}</p>
{/if}

<style>
p {
  color: #FF4B4B;
  font-size: 12px;
}
</style>
