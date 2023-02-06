<script>
  import Amount from "$lib/Amount.svelte";
  import TransactionHistory from "$lib/TransactionHistory.svelte";
  import { apiStore } from "$lib/api.js";

  export let donator_id;

  let activeTab = 'sent';
  const donatorStats = apiStore(`donator/${donator_id}/stats`, `donator:${donator_id}`);
</script>

<div class="history">
  <div class="tabs">
    <div><button disabled={activeTab === 'sent'} on:click={() => activeTab = 'sent'}>Sent</button></div>
    <div><button disabled={activeTab === 'received'} on:click={() => activeTab = 'received'}>Received</button></div>
  </div>
  <div class="totals">
  {#if $donatorStats}
    {@const {total_donated, total_claimed, total_received} = $donatorStats}
      <div style:display={activeTab === 'sent' ? 'block' : 'none'}>
        <span>You donated: </span>
        <Amount amount={total_donated} />
      </div>
      <div style:display={activeTab === 'sent' ? 'block' : 'none'}>
        <span>Users claimed: </span>
        <Amount amount={total_claimed} />
      </div>
      <div style:display={activeTab === 'received' ? 'block' : 'none'}>
        <span>You received: </span>
        <Amount amount={total_received} />
      </div>
    {/if}
  </div>
  <div style:display={activeTab === 'sent' ? 'block' : 'none'}>
    <TransactionHistory {donator_id} direction=sent />
  </div>
  <div style:display={activeTab === 'received' ? 'block' : 'none'}>
    <TransactionHistory {donator_id} direction=received />
  </div>
</div>

<style>
.history {
  display: flex;
  flex-direction: column;
  gap: 40px;
  overflow-x: scroll;
}
.tabs {
  display: flex;
  width: 100%;
  box-shadow: 0px 1px 0px rgba(0, 0, 0, 0.15);
}
.tabs div {
  width: 100%;
  display: flex;
  justify-content: center;
}
.tabs div button {
  width: 117px;
  height: 48px;
  background: none;
  border-width: 0;
  border-color: black;
  color: var(--color);
  font-weight: 500;
  font-size: 16px;
  line-height: 20px;
}
.tabs div button:disabled {
  border-width: 0 0 2px 0;
}
.tabs div button:enabled {
  cursor: pointer;
}
.totals {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}
.totals span {
  font-size: 14px;
  line-height: 20px;
}
.history::-webkit-scrollbar {
  display: none;  /* hide scroll for Safari and Chrome */
}
</style>
