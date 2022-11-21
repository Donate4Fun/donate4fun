<script>
  import Loading from "$lib/Loading.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import Section from "$lib/Section.svelte";
  import YoutubeVideo from "$lib/YoutubeVideo.svelte";
  import Donator from "$lib/Donator.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Separator from "$lib/Separator.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import LinkedItems from "$lib/LinkedItems.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import { me, reloadMe } from "$lib/session.js";
  import api from "$lib/api.js";
  import { link } from "svelte-navigator";
  import { toText } from "$lib/utils.js";
  import title from "$lib/title.js";

  export let donator_id;
  let itsMe;
  let donator;
  let donations;

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
    donations = await api.get(`donations/by-donator/${donator_id}`);
    return me;
  }
</script>

<Section>
  <div class="main">
    {#await load(donator_id, $me) then me}
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
          <ChannelLogo url={channel.thumbnail_url} size=40px />
          <div class="channel-name">
            <YoutubeChannel linkto="withdraw" channel={channel} />
          </div>
        </LinkedItems>
        <div style="height: 40px;"></div>
        <LinkedItems let:item={account} basePath="twitter" transferPath="account">
          <TwitterAccount account={account} />
        </LinkedItems>
      {:else}
        <p>{donator.name}</p>
        <Button link="/fulfill/{donator_id}">Donate</Button>
      {/if}
      <div class=transactions><Separator>History</Separator></div>
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
            <YoutubeChannel channel={donation.youtube_channel} class="ellipsis" linkto=withdraw logo />
          {:else if donation.twitter_account}
            <TwitterAccount account={donation.twitter_account} class="ellipsis" />
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 36px 24px 123px;
}
.balance-actions {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.channel-name {
  width: 100%;
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
