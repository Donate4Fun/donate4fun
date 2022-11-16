<script>
  import {link, useResolve} from "svelte-navigator";
  import Loading from "$lib/Loading.svelte";
  import Donator from "$lib/Donator.svelte";
  import Datetime from "$lib/Datetime.svelte";
  import Amount from "$lib/Amount.svelte";
  import Error from "$lib/Error.svelte";
  import Button from "$lib/Button.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import Section from "$lib/Section.svelte";
  import Infobox from "$lib/Infobox.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import api from "$lib/api.js";
  import { me, reloadMe } from "$lib/session.js";
  import title from "$lib/title.js";
  import { youtube_channel_url } from "$lib/utils.js";

  export let channel_id;

  let channel;
  let donations;
  let error;
  let showSuccess = false;
  let balance;
  let lnurl;
  let amount;
  let show_more_donations;

  const resolve = useResolve();

  async function load() {
    showSuccess = false;
    amount = null;
    try {
      channel = await api.get(`youtube/channel/${channel_id}`);
      $title = `Claim donations for ${channel.title} [${channel.id}]`
      donations = await api.get(`donations/by-donatee/${channel_id}`);
      return await me.get();
    } catch (err) {
      console.log(err)
      error = err.response.data.detail;
    }
  }

  async function claim() {
    await api.post(`youtube/channel/${channel_id}/transfer`);
    await load();
  }
</script>

<Section>
  <div class="youtube-channel">
    {#await load()}
      <Loading />
    {:then me}
      <h1>Donations to <YoutubeChannel channel={channel} /></h1>
      <ChannelLogo url={channel.thumbnail_url} />
      <div class="controls">
        <div class="available">Available to claim: <Amount amount={channel.balance} /></div>
        {#if channel.is_my}
          {#if me.connected}
            <Button disabled={channel.balance === 0} on:click={claim}>Take donations</Button>
          {:else}
            <Button link={resolve('/login')}></Button>
          {/if}
        {:else}
          <Infobox>You can withdraw donations if the channel belongs to you. Confirm by linking your Youtube channel.</Infobox>
          <Button link="/prove/youtube">Link your Youtube channel</Button>
        {/if}
        <Button class="want-more white" link={resolve("link")}>Want more donations?</Button>
      </div>
      <div class="table">
        <div class="head">
          <div>Name</div><div>Date</div><div>Amount</div>
        </div>
        <div class="body">
          {#each donations as donation}
            <Donator user={donation.donator} class="ellipsis"/>
            <Datetime dt={donation.paid_at} />
            <Amount amount={donation.amount} />
          {/each}
        </div>
      </div>
    {/await}
  </div>
</Section>

<style>
.youtube-channel {
  padding: 36px 70px 74px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
h1 {
  text-align: center;
  font-weight: 900;
  font-size: 24px;
}
.controls {
  display: flex;
  gap: 20px;
  flex-direction: column;
  align-items: center;
}
.table {
  font-size: 12px;
}
.head {
  color:  rgba(0, 0, 0, 0.6);
  text-align: left;
}
.body {
  font-weight: 500;
  padding: 0 1em 1em 1em;
}
.table .head,.table .body {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 200px 120px 99px;
  column-gap: 20px;
  row-gap: 26px;
}
</style>
