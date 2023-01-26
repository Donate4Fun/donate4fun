<script>
  import { readable } from "svelte/store";
  import { slide } from "svelte/transition";
  import { link } from "svelte-navigator";
  import Donator from "$lib/Donator.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";
  import Loader from "$lib/Loader.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import api from "$lib/api.js";

  export let socialProvider;
  export let accountId;

  function apiStore(getPath, topic) {
    return readable(null, set => {
      const ws = api.subscribe(topic);
      ws.on("notification", async (notification) => {
        if (notification.status === 'OK')
          set(await api.get(getPath));
      });
      (async () => {
        await ws.ready();
        set(await api.get(getPath));
      })();
      return () => ws.close();
    });
  }

  const donations = apiStore(
    `social/${socialProvider}/${accountId}/donations/by-donatee`,
    `social:${socialProvider}:${accountId}`,
  );
</script>

<div class="table">
  <h1 class="title">Latest donations</h1>
  <div class="head row">
    <div>Name</div><div>Date</div><div>Amount</div>
  </div>
  <div class="body">
    {#if $donations}
      {#each $donations as donation (donation.id)}
        <div class="row" transition:slide|local>
          {#if donation.donator_twitter_account}
            <TwitterAccount account={donation.donator_twitter_account} --image-size=24px />
          {:else}
            <Donator user={donation.donator} ellipsis />
          {/if}
          <a use:link href="/donation/{donation.id}">
            <Datetime dt={donation.paid_at} />
          </a>
          <Amount amount={donation.amount} />
        </div>
      {/each}
    {:else}
      <Loader />
    {/if}
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
  display: flex;
  flex-direction: column;
  gap: 26px;
}
.table .head,.table .body {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
}
.table .title {
  text-align: center;
}
.table {
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 26px;
  align-items: center;
}
.table .row {
  display: grid;
  grid-template-columns: 200px 120px 99px;
  column-gap: 20px;
  align-items: center;
}
</style>
