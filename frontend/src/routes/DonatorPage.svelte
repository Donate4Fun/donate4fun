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
</script>

{#await load(donator_id, $me)}
  <Loader />
{:then me}
  <Section>
    <div class="main">
      <Userpic user={donator} class="userpic" --width=88px/>
      {#if itsMe}
        <div style="height: 21px;"></div>
        <MeNamePubkey align="center" />
        <div style="height: 32px;"></div>
        <div class="balance-actions">
          {#if me.connected}
            <MeBalance />
          {:else}
            <Button link="/login">Connect a wallet</Button>
          {/if}
        </div>
        <div style="height: 56px;"></div>
        <LinkedItems let:item={channel} basePath="youtube" transferPath="channel">
          <div class="linked-item">
            <YoutubeChannel linkto="withdraw" channel={channel} logo --gap=16px />
          </div>
        </LinkedItems>
        <div style="height: 40px;"></div>
        <LinkedItems let:item={account} basePath="twitter" transferPath="account">
          <div class="linked-item">
            <TwitterAccount account={account} --gap=16px />
          </div>
        </LinkedItems>
      {:else}
        <p>{donator.name}</p>
        <Button link="/fulfill/{donator_id}">Donate</Button>
      {/if}
      <div class=transactions><Separator>History</Separator></div>
      <TransactionHistory {donator_id} />
    </div>
  </Section>
{/await}

<style>
.main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 36px 34px;
  width: 640px;
}
.balance-actions {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.linked-item {
  width: 100%;
}
.transactions {
  margin-top: 56px;
  margin-bottom: 32px;
  width: 100%;
}
</style>
