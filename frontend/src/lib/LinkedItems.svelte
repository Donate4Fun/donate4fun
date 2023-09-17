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
  import { syncMe as me } from "$lib/session.js";
  import { cLog, cError } from "$lib/log.js";
  import { notify } from "$lib/notifications.js";

  export let socialProvider = null;
  export let name;
  export let items = [];

  async function collect(item) {
    await api.post(`social/${socialProvider}/${item.id}/transfer`);
  }

  const itemsStore = derived(me, ($me, set) => {
    if (socialProvider === null || $me === null)
      return;
    const ws = api.subscribe(`donator:${$me.donator.id}`);
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        set(await api.get(`social/${socialProvider}/linked`));
      }
    });
    (async () => {
      try {
        await ws.ready();
        set(await api.get(`social/${socialProvider}/linked`));
      } catch (err) {
        cError("Failed to load linked items", err);
        if (err.target instanceof WebSocket && err.type === 'error')
          notify("Network error", "WebSocket error in linked items store", "error");
      }
    })();
    return () => {
      ws.close();
    };
  }, items);

  async function unlink(item) {
    await api.post(`social/${socialProvider}/${item.id}/unlink`);
  }
  export let onUnlink = unlink;
</script>

<div class="container">
  {#if $itemsStore.length > 0}
    <h2 transition:slide|local>
      <slot name="header">
        Linked <b>{name}</b> accounts:
      </slot>
    </h2>
    <ul>
      {#each $itemsStore as item (item.id)}
        <li transition:slide|local>
          <slot name="item" {item} />
          {#if item.balance > 0}
            <Amount amount={item.balance} />
          {/if}
          <div class="buttons">
            {#if item.balance > 0}
              <Button on:click={() => collect(item)} --border-width=0 padding="0 24px">Claim</Button>
            {/if}
            <HoldButton
              --border-width=0
              on:click={() => onUnlink(item)}
              tooltipText="Hold to unlink"
            ><span class="unlink">Unlink</span></HoldButton>
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
