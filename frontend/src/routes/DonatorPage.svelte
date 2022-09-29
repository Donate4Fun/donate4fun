<script>
  import Loading from "../lib/Loading.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Donator from "../lib/Donator.svelte";
  import Amount from "../lib/Amount.svelte";
  import FiatAmount from "../lib/FiatAmount.svelte";
  import Button from "../lib/Button.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Separator from "../lib/Separator.svelte";
  import MeNamePubkey from "../lib/MeNamePubkey.svelte";
  import MeBalance from "../lib/MeBalance.svelte";
  import {me} from "../lib/session.js";
  import api from "../lib/api.js";

  import { link } from "svelte-navigator";

  export let donator_id;
  let donations;
  let donator;

  async function load() {
    if (donator_id === $me.donator?.id) {
      await $me.load();
      donator = $me.donator;
    } else {
      donator = await api.get(`donator/${donator_id}`)
    }
    donations = await api.get(`donations/by-donator/${donator_id}`);
  }

  async function donate() {
    navigate(`/fulfill/${donator.id}`);
  }
</script>

<Page>
  <Section class="donator-main flex-column align-center gap-8">
  {#await load()}
    <Loading/>
  {:then}
    <Userpic user={donator} class="userpic" --width=88px/>
    {#if $me.donator.id === donator.id}
      <div style="height: 21px;"></div>
      <MeNamePubkey />
      <div style="height: 32px;"></div>
      <MeBalance />
    {:else}
      <p>{donator.name}</p>
      <Button link="/fulfill/{donator_id}">Donate</Button>
    {/if}
    <div class=transactions><Separator>Transactions</Separator></div>
    <div class="table">
      <div class="head">
        <div>When</div>
        <div>Whom</div>
        <div>Amount</div>
        <div>Status</div>
      </div>
      {#each donations as donation}
        {#if donation.paid_at}
          <Datetime dt={donation.paid_at}/>
        {:else}
          <Datetime dt={donation.created_at}/>
        {/if}
        {#if donation.youtube_channel}
          <YoutubeChannel channel={donation.youtube_channel} linkto=donate class="ellipsis" />
        {:else}
          <Donator user={donation.receiver} ellipsis --gap=5px />
        {/if}
        <Amount amount={donation.amount}/>
        <div>
          {#if donation.paid_at}
            {#if donation.donator.id === donation.receiver?.id}
              Received
            {:else}
              Paid
            {/if}
          {:else}
            Unpaid
          {/if}
        </div>
      {/each}
    </div>
  {/await}
  </Section>
</Page>

<style>
:global(.donator-main) {
  padding: 36px 119px 123px;
  width: 640px;
}
.transactions {
  margin-top: 56px;
  margin-bottom: 32px;
  width: 100%;
}
.table .head {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 109px 99px 83px 45px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
