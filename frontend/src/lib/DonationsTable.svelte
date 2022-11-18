<script>
  import Donator from "$lib/Donator.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";

  export let donations;
</script>

<div class="table">
  <h1 class="title">Latest donations</h1>
  <div class="head">
    <div>Name</div><div>Date</div><div>Amount</div>
  </div>
  <div class="body">
    {#each donations as donation}
      <Donator user={donation.donator} ellipsis />
      <Datetime dt={donation.paid_at} />
      <Amount amount={donation.amount} />
    {/each}
  </div>
</div>

<style>
.head {
  color:  rgba(0, 0, 0, 0.6);
  text-align: left;
}
.body {
  font-weight: 500;
  padding: 0 1em 1em 1em;
}
.table .head,.table .body {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table .title {
  grid-column: 1 / span 3;
  text-align: center;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 200px 120px 99px;
  column-gap: 20px;
  row-gap: 26px;
  align-items: center;
}
</style>
