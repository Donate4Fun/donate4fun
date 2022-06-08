<script>
  import axios from 'axios';
  import Donation from "../lib/Donation.svelte";
  import Spinner from "../lib/Spinner.svelte";

  export let id;
  let donation;

  const loadDonation = async () => {
    const resp = await axios.get(`/api/v1/donation/${id}`);
    const data = resp.json();
  }
</script>

{#await loadDonation()}
<Spinner />Loading...
{:then}
<Donation {...donation} />
{/await}
