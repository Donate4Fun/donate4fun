<script>
  import { link } from "svelte-navigator";

  import Button from "$lib/Button.svelte";
  import Amount from "$lib/Amount.svelte";
  import api from "$lib/api.js";
  import { capitalize } from "$lib/utils.js";

  export let items;
  export let basePath;
  export let transferPath;

  async function collect(item) {
    await api.post(`${basePath}/${transferPath}/${item.id}/transfer`);
    await load();
  }

  async function load() {
    items = await api.get(`${basePath}/linked`);
  }
</script>

<div class="container">
  <div class="header">
    <h2>Linked <b>{capitalize(basePath)}</b> accounts:</h2>
    <a use:link href="/{basePath}/prove">Add</a>
  </div>
  {#await load() then}
    <ul>
      {#each items as item}
      <li>
        <slot {item} />
        <Amount amount={item.balance} />
        <div class="withdraw-button">
          <Button disabled={item.balance === 0} on:click={() => collect(item)} --border-width=0>Claim</Button>
        </div>
      </li>
      {/each}
    </ul>
  {/await}
</div>

<style>
.container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header > h2 {
  font-weight: 500;
  font-size: 18px;
  line-height: 24px;
  font-size: 20px;
}
.header > a {
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
}
ul {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 8px;
  padding: 0;
}
li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 17px;
  padding: 16px;
  padding-right: 0;
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
.withdraw-button {
  height: 44px;
  justify-self: end;
  flex-grow: 1;
}
</style>
