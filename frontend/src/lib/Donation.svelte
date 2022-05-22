<script>
  export let donatee;
  export let amount;
  export let donated_at;
  export let claimed_at;
</script>
<main>
  {donatee} donated {amount} sats at {donated_at}.
  {#if claimed_at}
    Claimed at {claimed_at}
  {:else}
    Unclaimed
  {/if}
</main>
