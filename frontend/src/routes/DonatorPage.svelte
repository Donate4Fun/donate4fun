<script>
  import Loading from "../lib/Loading.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Donator from "../lib/Donator.svelte";
  import Amount from "../lib/Amount.svelte";
  import Button from "../lib/Button.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Separator from "../lib/Separator.svelte";
  import {me} from "../lib/session.js";
  import api from "../lib/api.js";

  import { link } from "svelte-navigator";

  export let donator_id;
  let donations;
  let donator;

  async function load() {
    donator = await api.get(`donator/${donator_id}`)
    donations = await api.get(`donations/by-donator/${donator_id}`);
  }

  async function donate() {
    navigate(`/fulfill/${donator.id}`, {state: response});
  }
</script>

<Page>
  <Section class="donator-main">
  {#await load()}
    <Loading/>
  {:then}
    <Userpic {...donator} class="userpic" />
    {#if $me.donator.id === donator.id}
      <div class="balance">Balance: <Amount amount={donator.balance} /> <Button link="/fulfill/{donator_id}">Fulfill</Button></div>
    {:else}
      <div class="balance"><Button link="/fulfill/{donator_id}">Fulfill</Button></div>
    {/if}
    <div class="name">{donator.name}</div>
    <div class=transactions><Separator>Transactions</Separator></div>
    <div class="table">
      <div class="head">
        <div>When</div>
        <div>Whom</div>
        <div>Amount</div>
        <div>Status</div>
      </div>
      {#each donations as donation}
        <a href="/donation/{donation.id}" use:link>
          {#if donation.paid_at}
            <Datetime dt={donation.paid_at}/>
          {:else}
            <Datetime dt={donation.created_at}/>
          {/if}
        </a>
        {#if donation.youtube_channel}
          <YoutubeChannel {...donation.youtube_channel} linkto=donate class="ellipsis" />
        {:else}
          <Donator user={donation.receiver} class=ellipsis />
        {/if}
        <Amount amount={donation.amount}/>
        <div>
          {#if donation.paid_at}
          Paid
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
  padding: 36px 158px 123px 158px;
  width: 718px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
:global(.donator-main .userpic img) {
  width: 88px;
}
.name {
  margin-top: 24px;
  font-weight: 500;
  font-size: 16px;
}
.transactions {
  margin-top: 64px;
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
  grid-template-columns: 109px 69px 83px 69px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
