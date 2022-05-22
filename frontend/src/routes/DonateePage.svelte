<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Loading from "../lib/Loading.svelte";
  import Donation from "../lib/Donation.svelte";

  export let donatee;
  let sum_donated;
  let sum_unclaimed;
  let donations;
  let error;
  const min_claim_limit = 100;
  $: isClaimAllowed = sum_unclaimed >= min_claim_limit;

  const load = async () => {
    ({ sum_donated, sum_unclaimed, donations } = await axios.get(`/api/v1/donatee/${donatee}`));
  }
  const claim = async () => {
    try {
      const { withdrawReq } = await axios.post("/api/v1/claim", {donatee: donatee});
      // TODO: show QR with lnurl
    } catch (err) {
      console.error(err)
      error = err;
    }
  }
</script>

<main>
  {#await load}
  <Loading />
  {:then}
  Donatee {donatee} has total {sum_donated} sats donated. Unclaimed {sum_unclaimed}.
  <button disabled={!isClaimAllowed} on:click={claim}>Claim</button>
  Want to support him? <a href="/donate/{donatee}">Donate</a>
  <ul>
    {#each donations as donation}
    <li>
      <Donation {...donation} />
    </li>
    {/each}
  </ul>
  {/await}
</main>
