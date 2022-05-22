<script>
  import axios from 'axios';
  import Donation from "../lib/Donation.svelte";

  export let id;
  let donation;
  const loadDonation = async () => {
    ({donation} = await axios.get(`/api/v1/donation/${id}`).json())
  }
</script>
{#await loadDonation()}
Loading...
{:then}
<Donation {...donation} />
{/await}
