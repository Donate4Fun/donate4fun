<script>
  export let amount;
  export let claimed_at;
  export let donator;
  export let donator_id;
  export let r_hash;
  export let id;
  export let trigger;
  export let paid_at;
  export let created_at;
  export let message;
  export let youtube_channel;
</script>
<main>
  {donator.name} donated {amount} sats to {youtube_channel.channel_id} at {paid_at}.
  {#if claimed_at}
    Claimed at {claimed_at}
  {:else}
    Unclaimed
  {/if}
</main>
