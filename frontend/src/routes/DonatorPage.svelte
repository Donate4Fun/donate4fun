<script>
  import Header from "../lib/Header.svelte";
  import Footer from "../lib/Footer.svelte";
  import Loading from "../lib/Loading.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Section from "../lib/Section.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Amount from "../lib/Amount.svelte";
  import Datetime from "../lib/Datetime.svelte";
  import {me} from "../lib/session.js";
  import api from "../lib/api.js";

  import { link } from "svelte-navigator";

  let donations;

  async function load() {
    await me.init();
    donations = await api.get(`donations/by-donator/${$me.donator.id}`);
  }
</script>

<Header/>
{#await load()}
<Loading/>
{:then}
<Section>
  <h1><Userpic {...$me.donator}/> {$me.donator.name}</h1>
  <table>
    <thead><tr><th>When<th>Whom<th>Amount</tr></thead>
    <tbody>
    {#each donations as donation}
      <tr><td><a href="/donation/{donation.id}" use:link>
      {#if donation.paid_at}
      <Datetime dt={donation.paid_at}/>
      {:else}
      unpaid
      {/if}
      </a>
      <td><YoutubeChannel {...donation.youtube_channel}/><td><Amount amount={donation.amount}/></tr>
    {/each}
    </tbody>
  </table>
</Section>
{/await}
<Footer/>

<style>
h1 {
  display: flex;
  align-items: center;
  gap: 1em;
}
th {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
}
table {
  font-size: 12px;
}

</style>
