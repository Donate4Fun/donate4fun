<script>
  import Loading from "../lib/Loading.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import YoutubeVideo from "../lib/YoutubeVideo.svelte";
  import Donator from "../lib/Donator.svelte";
  import Amount from "../lib/Amount.svelte";
  import FiatAmount from "../lib/FiatAmount.svelte";
  import Button from "../lib/Button.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import Separator from "../lib/Separator.svelte";
  import MeNamePubkey from "../lib/MeNamePubkey.svelte";
  import MeBalance from "../lib/MeBalance.svelte";
  import { me, reloadMe } from "../lib/session.js";
  import api from "../lib/api.js";
  import { link } from "svelte-navigator";
  import { toText } from "$lib/utils.js";

  export let donator_id;
  export let navigate;
  let itsMe;
  let donator;
  let donations;

  async function load(donator_id, me) {
    const mee = await me;
    itsMe = donator_id === mee.donator?.id;
    if (itsMe) {
      await reloadMe();
      donator = mee.donator;
    } else
      donator = await api.get(`donator/${donator_id}`);
    donations = await api.get(`donations/by-donator/${donator_id}`);
  }

  async function donate() {
    navigate(`/fulfill/${donator.id}`);
  }
</script>

<Section>
  <div class="flex-column align-center gap-8 main">
    {#await load(donator_id, $me)}
      <Loading/>
    {:then}
      <Userpic user={donator} class="userpic" --width=88px/>
      {#if itsMe}
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
          <div>Date</div>
          <div>Donatee</div>
          <div>Amount</div>
          <div>Status</div>
        </div>
        {#each donations as donation}
          {#if donation.paid_at}
            <Datetime dt={donation.paid_at}/>
          {:else}
            <Datetime dt={donation.created_at}/>
          {/if}
          {#if donation.youtube_video}
            <YoutubeVideo video={donation.youtube_video} />
          {:else if donation.youtube_channel}
            <YoutubeChannel channel={donation.youtube_channel} class="ellipsis" logo />
          {:else}
            <Donator user={donation.receiver} ellipsis --gap=5px />
          {/if}
          <Amount amount={toText(donation.amount)}/>
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
  </div>
</Section>

<style>
.main {
  padding: 36px 119px 123px;
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
  grid-template-columns: 109px 199px 83px 45px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
