<script>
  import { link } from "svelte-navigator";
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";
  import Section from "../lib/Section.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Donator from "../lib/Donator.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";
  import api from "../lib/api.js";

  let donations = [];

  const loadDonations = async () => {
    donations = await api.get("donations/latest");
  }
</script>

<Section class="donations">
  <h1>Donations <span class="annotation">Last <b>24 hours</b></span></h1>
  {#await loadDonations()}
    <Loading />
  {:then}
    <div class="table">
      <div class="head">
        <div>Who</div><div>When</div><div>Amount</div><div>Blogger</div>
      </div>
      {#each donations as donation}
        <div class=blogger>
          <ChannelLogo url={donation.youtube_channel.thumbnail_url} size=28px />
          {#if donation.youtube_video}
          <div class=vcenter title="{donation.youtube_video.title}"><a href="/donate/{donation.youtube_channel.id}" class="ellipsis" use:link>{donation.youtube_channel.title}</a></div>
          {:else}
          <div class=vcenter><a href="/donate/{donation.youtube_channel.id}" class="ellipsis" use:link>{donation.youtube_channel.title}</a></div>
          {/if}
        </div>
        <div class=vcenter><Datetime dt={donation.paid_at} /></div>
        <div class=vcenter><Amount amount={donation.amount} /></div>
        <Donator user={donation.donator} class="ellipsis" />
      {/each}
    </div>
    <div class=fadeout></div>
  {/await}
</Section>

<style>
:global(.donations) {
  width: 537px;
  height: 501px;
  padding: 36px 12px 0 36px;
  display: grid;
  overflow: hidden;
  position: relative;
}
@media only screen and (max-width: 1280px) {
  :global(.donations) {
    width: 640px;
  }
}
@media only screen and (max-width: 640px) {
  :global(.donations) {
    width: 100%;
  }
}
h1 {
  margin-top: 0px;
  margin-bottom: 32px !important;
}
.annotation {
  font-weight: 400;
  font-size: 12px;
  margin-left: 16px;
}
.vcenter {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
:global(.amount) {
  margin: 0;
}
.table {
  display: grid;
  grid-template-columns: 158px 109px 80px 168px;
  column-gap: 20px;
  row-gap: 26px;
  font-size: 12px;
  text-align: left;
  line-height: 15px;
  overflow: scroll;
}
.head {
  color: rgba(0, 0, 0, 0.6);
  display: contents;
}
:global(.ellipsis) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fadeout {
  position : absolute;
  z-index  : 1;
  bottom   : 0;
  left     : 0;
  pointer-events   : none;
  background-image : linear-gradient(to bottom,
                    rgba(255,255,255, 0),
                    rgba(255,255,255, 1) 90%);
  width    : 100%;
  height   : 4em;
}
.blogger {
  display: flex;
  align-items: center;
  gap: 5px;
}
</style>
