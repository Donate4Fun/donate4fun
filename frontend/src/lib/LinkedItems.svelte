<script>
  import { derived } from "svelte/store";
  import { slide } from "svelte/transition";
  import { link } from "svelte-navigator";
  import { asyncable } from 'svelte-asyncable';

  import Button from "$lib/Button.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import Amount from "$lib/Amount.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import api from "$lib/api.js";
  import { capitalize } from "$lib/utils.js";
  import { me } from "$lib/session.js";

  export let basePath = null;
  export let transferPath;
  export let name;
  export let items = [];

  async function collect(item) {
    await api.post(`${basePath}/${transferPath}/${item.id}/transfer`);
  }

  const itemsStore = derived(me, async ($me, set) => {
    if (basePath === null)
      return;
    const me_ = await $me;
    const ws = api.subscribe(`donator:${me_.donator.id}`, { autoReconnect: false });
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        set(await api.get(`${basePath}/linked`));
      }
    });
    await ws.ready();
    set(await api.get(`${basePath}/linked`));
    return () => {
      ws.close();
    };
  }, items);

  async function unlink(item) {
    await api.post(`${basePath}/${transferPath}/${item.id}/unlink`);
  }
  export let onUnlink = unlink;
</script>

<div class="container">
  {#if $itemsStore.length > 0}
    <h2 transition:slide>
      <slot name="header">
        Linked <b>{name}</b> accounts:
      </slot>
    </h2>
    <ul>
      {#each $itemsStore as item (item.id)}
        <li transition:slide>
          <slot name="item" {item} />
          {#if item.balance > 0}
            <Amount amount={item.balance} />
          {/if}
          <div class="buttons">
            {#if item.balance > 0}
              <Button on:click={() => collect(item)} --border-width=0 padding="0 24px">Claim</Button>
            {/if}
            {#if item.via_oauth}
              <HoldButton
                --border-width=0
                on:click={() => onUnlink(item)}
                tooltipText="Hold to unlink"
              ><span class="unlink">Unlink</span></HoldButton>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}
  <slot name=add />
</div>

<style>
.container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
h2 {
  font-weight: 500;
  line-height: 24px;
  font-size: 18px;
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
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
.buttons {
  height: 44px;
  flex-grow: 1;
  display: flex;
  gap: 8px;
}
.unlink {
  padding: 0 24px;
}
</style>
