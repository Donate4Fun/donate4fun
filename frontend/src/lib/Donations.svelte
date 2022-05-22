<script>
import Loading from "../lib/Loading.svelte";
import Donation from "../lib/Donation.svelte";
import Section from "../lib/Section.svelte";
import axios from "axios";

let donations = [];

const loadDonations = async () => {
  ({ donations } = await asios.get("/api/v1/donations/latest").json());
}
</script>

<Section>
  <h1>Latest donations</h1>
  <main>
  {#await loadDonations}
    <Loading />
  {:then}
    <ul>
      {#each donations as donation}
      <li>
        <Donation {...donation} />
      </li>
      {/each}
    </ul>
  {/await}
  </main>
</Section>
