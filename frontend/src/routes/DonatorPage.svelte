<script>
  import { link } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import Section from "$lib/Section.svelte";
  import Donator from "$lib/Donator.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Separator from "$lib/Separator.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import LinkedItems from "$lib/LinkedItems.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import TransactionHistory from "$lib/TransactionHistory.svelte";
  import { me, reloadMe } from "$lib/session.js";
  import api from "$lib/api.js";
  import title from "$lib/title.js";

  export let donator_id;
  let itsMe;
  let donator;
  let activeTab = 'sent';

  async function load(donator_id, me_) {
    const me = await me_;
    itsMe = donator_id === me.donator?.id;
    if (itsMe) {
      await reloadMe();
      donator = me.donator;
    } else {
      donator = await api.get(`donator/${donator_id}`);
    }
    title.set(`Donator profile for ${donator.name}`);
    return me;
  }

  async function loadTotals() {
    return await api.get(`donator/${donator.id}/stats`);
  }
</script>

{#await load(donator_id, $me)}
  <Loader />
{:then me}
  <Section>
    <div class="main">
      <div class="top-block">
        <div class="image-and-name">
          <Userpic user={donator} class="userpic" --width=88px/>
          {#if itsMe}
            <MeNamePubkey align="center" />
          {:else}
            <p>{donator.name}</p>
          {/if}
        </div>
        {#if itsMe}
          <div class="balance-actions">
            {#if me.connected}
              <MeBalance />
            {:else}
              <Button link="/login">Connect a wallet</Button>
            {/if}
          </div>
        {:else}
          <Button link="/fulfill/{donator_id}">Donate</Button>
        {/if}
      </div>
      {#if itsMe}
        <div class="linked">
          <LinkedItems let:item={channel} basePath="youtube" transferPath="channel">
            <div class="linked-item">
              <YoutubeChannel linkto="withdraw" channel={channel} logo --gap=16px />
            </div>
          </LinkedItems>
          <LinkedItems let:item={account} basePath="twitter" transferPath="account">
            <div class="linked-item">
              <TwitterAccount account={account} --gap=16px />
            </div>
          </LinkedItems>
        </div>
        <div class="history">
          <div class="tabs">
            <div><button disabled={activeTab === 'sent'} on:click={() => activeTab = 'sent'}>Sent</button></div>
            <div><button disabled={activeTab === 'received'} on:click={() => activeTab = 'received'}>Received</button></div>
          </div>
          <div class="totals">
            {#await loadTotals()}
              <Loader />
            {:then {total_donated, total_claimed, total_received}}
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
            {/await}
          </div>
          <div style:display={activeTab === 'sent' ? 'block' : 'none'}>
            <TransactionHistory {donator_id} direction=sent />
          </div>
          <div style:display={activeTab === 'received' ? 'block' : 'none'}>
            <TransactionHistory {donator_id} direction=received />
          </div>
        </div>
      {/if}
    </div>
  </Section>
{/await}

<style>
.main {
  display: flex;
  flex-direction: column;
  gap: 64px;
  padding: 36px 34px;
}
@media (max-width: 639px) {
  .main {
    width: 100vw;
  }
}
@media (min-width: 640px) {
  .main {
    width: 640px;
    align-items: center;
  }
}
.top-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}
.image-and-name {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.linked {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 44px;
  overflow-x: scroll;
  width: 100%;
}
.linked-item {
  flex-grow: 100;
}
.balance-actions {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
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
</style>
