<script>
  import { link, useNavigate } from "svelte-navigator";

  import Userpic from "$lib/Userpic.svelte";
  import Section from "$lib/Section.svelte";
  import Donator from "$lib/Donator.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import Title from "$lib/Title.svelte";
  import TransactionHistory from "$lib/TransactionHistory.svelte";
  import { syncMe as me } from "$lib/session.js";
  import { apiStore } from "$lib/api.js";
  import title from "$lib/title.js";

  export let donator_id;
  let activeTab = 'sent';

  const donator = apiStore(`donator/${donator_id}`, `donator:${donator_id}`);
  const donatorStats = apiStore(`donator/${donator_id}/stats`, `donator:${donator_id}`);
  $: itsMe = donator_id === $me?.donator?.id;
</script>

{#if $donator}
  <Title title="Donator profile for {$donator.name}" />
  <Section>
    <div class="main">
      {#if itsMe}
        <div class="settings-button">
          <BaseButton
            --border-width=1px
            --border-color="rgba(0, 0, 0, 0.2)"
            --width=115px
            --height=32px
            --text-color=black
            --font-weight=500
            --font-size=12px
            link="/settings"
          >Settings</BaseButton>
        </div>
      {/if}
      <div class="top-block">
        <div class="image-and-name">
          <Userpic user={$donator} class="userpic" --width=88px/>
          {#if itsMe}
            <MeNamePubkey align="center" />
          {:else}
            <p>{$donator.name}</p>
          {/if}
        </div>
        {#if itsMe}
          <div class="balance-actions">
            {#if $me.connected}
              <MeBalance />
            {:else}
              <Button link="/signin">Sign in</Button>
            {/if}
          </div>
        {:else}
          <Button link="/fulfill/{donator_id}">Donate</Button>
        {/if}
      </div>
      {#if itsMe}
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
      {/if}
    </div>
  </Section>
{/if}

<style>
.main {
  display: flex;
  flex-direction: column;
  gap: 64px;
  padding: 40px 34px;
  position: relative;
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
.settings-button {
  position: absolute;
  right: 24px;
  top: 24px;
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
  gap: 24px;
}
.balance-actions {
  width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
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
.history::-webkit-scrollbar {
  display: none;  /* hide scroll for Safari and Chrome */
}
</style>
