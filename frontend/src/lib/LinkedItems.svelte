<script>
  import Button from "$lib/Button.svelte";
  import Amount from "$lib/Amount.svelte";
  import api from "$lib/api.js";

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
    <h2>Linked <b>Twitter</b> accounts:</h2>
  </div>
  {#await load() then}
    <ul>
      {#each items as item}
      <li>
        <slot {item} />
        <Amount amount={item.balance} />
        <div class="withdraw-button">
          <Button disabled={item.balance === 0} on:click={() => collect(item)} --border-width=0>Collect</Button>
        </div>
      </li>
      {/each}
      <li class="add">
        <Button --width=170px class="white" link="/{basePath}/prove">Add more</Button>
      </li>
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
h2 {
  font-size: 20px;
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
  gap: 17px;
  padding: 16px;
  height: 72px;
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
li.add {
  justify-content: center;
  background: none;
  height: 48px;
}
.withdraw-button {
  height: 44px;
  justify-self: end;
}
</style>
