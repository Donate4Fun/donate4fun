<script>
  import { syncMe as me } from "$lib/session.js";

  export let donation;
</script>

<div class="status">
  {#if donation.paid_at}
    {#if donation.cancelled_at}
      <span class="cancelled">Cancelled</span>
    {:else if donation.donator.id === donation.receiver?.id}
      Deposited
    {:else if donation.receiver?.id === $me?.donator.id}
      Received
    {:else if donation.receiver}
      Sent
    {:else if donation.lightning_address}
      <span class="success">Via ⚡@</span>
    {:else if donation.claimed_at}
      <span class="success">Claimed</span>
    {:else}
      Pending
    {/if}
  {:else}
    Unpaid
  {/if}
</div>

<style>
.status {
  font-weight: 500;
  font-size: 12px;
  line-height: 15px;
}
.cancelled {
  color: #FF472E;
}
.success {
  color: #19B400;
}
</style>
