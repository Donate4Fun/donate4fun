<script>
import Loading from "../lib/Loading.svelte";
import Donation from "../lib/Donation.svelte";
import Section from "../lib/Section.svelte";
import Amount from "../lib/Amount.svelte";
import YoutubeChannel from "../lib/YoutubeChannel.svelte";
import Donator from "../lib/Donator.svelte";
import api from "../lib/api.js";

let donations = [];

const loadDonations = async () => {
  donations = await api.get("donations/latest");
}
</script>

<Section>
  <h1>Donations <span class="annotation">Last <b>24 hours</b></span></h1>
  <main>
  {#await loadDonations()}
    <Loading />
  {:then}
    <table>
      <thead>
        <tr><th>Name<th>Amount<th>Date<th>Blogger
      </thead>
      <tbody>
      {#each donations as donation}
        <tr><td class="donator"><Donator user={donation.donator}/><td><Amount amount={donation.amount}/><td>{donation.paid_at}<td><YoutubeChannel {...donation.youtube_channel}/></tr>
      {/each}
      </tbody>
    </table>
  {/await}
  </main>
</Section>

<style>
.annotation {
  font-weight: 400;
  font-size: 12px;
}
th {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
}
table {
  font-size: 12px;
}
</style>
