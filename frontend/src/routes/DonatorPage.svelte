<script>
  import Loading from "../lib/Loading.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Amount from "../lib/Amount.svelte";
  import Datetime from "../lib/Datetime.svelte";
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
</script>

<Page>
  <Section class="donator-main">
  {#await load()}
    <Loading/>
  {:then}
    <Userpic {...donator} class="userpic" />
    <div class="name">{donator.name}</div>
    <div class="transactions"><span>Transactions<span></div>
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
        <YoutubeChannel {...donation.youtube_channel} linkto=donate class="ellipsis" />
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
  background: linear-gradient(180deg, 
    rgba(0,0,0,0) calc(50% - 1px), 
    rgba(0,0,0,0.1) calc(50%), 
    rgba(0,0,0,0) calc(50% + 1px)
  );
  margin-top: 64px;
  margin-bottom: 32px;
  width: 100%;
  text-align: center;
}
.transactions > span {
  background: white;
  padding: 0 6px;
  font-weight: 500;
  font-size: 16px;
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
