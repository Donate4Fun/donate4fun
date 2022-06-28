<script>
import Loading from "../lib/Loading.svelte";
import Donation from "../lib/Donation.svelte";
import Section from "../lib/Section.svelte";
import Amount from "../lib/Amount.svelte";
import YoutubeChannel from "../lib/YoutubeChannel.svelte";
import Donator from "../lib/Donator.svelte";
import Datetime from "../lib/Datetime.svelte";
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
      <div class="body">
      {#each donations as donation}
        <div class="row">
          <Donator user={donation.donator} class="ellipsis" />
          <div><Datetime dt={donation.paid_at} /></div>
          <div class="vcenter"><Amount amount={donation.amount} /></div>
          <div class="vcenter"><YoutubeChannel {...donation.youtube_channel} class="ellipsis"/></div>
        </div>
      {/each}
      </div>
    </div>
  {/await}
</Section>

<style>
:global(.donations) {
  width: 462px;
  height: 501px;
  padding: 36px 31px 37px 36px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
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
  grid-template-columns: 128px 57px 80px 69px;
  column-gap: 20px;
  row-gap: 26px;
  font-size: 12px;
  text-align: left;
  line-height: 15px;
}
.head {
  color: rgba(0, 0, 0, 0.6);
}
.head,.body,.row {
  display: contents;
}
:global(.ellipsis) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
