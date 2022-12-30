<script>
  import { link } from "svelte-navigator";
  import { asyncable } from 'svelte-asyncable';

  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import Amount from "$lib/Amount.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import api from "$lib/api.js";
  import { capitalize } from "$lib/utils.js";
  import { me } from "$lib/session.js";

  export let basePath;
  export let transferPath;
  export let name;

  async function collect(item) {
    await api.post(`${basePath}/${transferPath}/${item.id}/transfer`);
  }

  const linkedStore = asyncable(async (set, me_) => {
    const me = await me_;
    const ws = api.subscribe(`donator:${me.donator.id}`, { autoReconnect: false });
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        set(await api.get(`${basePath}/linked`));
      }
    });
    await ws.ready();
    set(await api.get(`${basePath}/linked`));
    return async () => {
      await ws.close();
    };
  }, null, [ me ]);

  async function unlink(item) {
    await api.post(`${basePath}/${transferPath}/${item.id}/unlink`);
  }
</script>

<div class="container">
  <div class="header">
    <h2>Linked <b>{name}</b> accounts:</h2>
  </div>
  {#await $linkedStore then items}
    <ul>
      {#each items as item}
      <li>
        <slot name="item" {item} />
        <Amount amount={item.balance} />
        <div class="withdraw-button">
          <Button disabled={item.balance === 0} on:click={() => collect(item)} --border-width=0 --padding="0 24px">Claim</Button>
          {#if item.via_oauth}
            <GrayButton on:click={() => unlink(item)} --padding="0 24px">Unlink</GrayButton>
          {/if}
        </div>
      </li>
      {/each}
      <li class="add">
        <SocialSigninButton type={basePath} width=300px>Add {name} account</SocialSigninButton>
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
.header > h2 {
  font-weight: 500;
  line-height: 24px;
  font-size: 18px;
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
li.add {
  justify-content: center;
  background: transparent;
}
.withdraw-button {
  height: 44px;
  justify-self: end;
  flex-grow: 1;
  display: flex;
  gap: 8px;
}
</style>
