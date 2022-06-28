<script>
  import axios from "axios";

  export let amount;
  let rate;
  $: usd_amount = (amount * rate).toFixed(3);

  async function load() {
    const resp = await axios.get("https://api.alternative.me/v2/ticker/bitcoin/");
    rate = resp.data.data["1"].quotes.USD.price / 100000000;
  }
</script>

<span>
≈${#await load()}
{:then}
{usd_amount}
{/await}
</span>

<style>
span {
  font-size: 12px;
}
</style>
