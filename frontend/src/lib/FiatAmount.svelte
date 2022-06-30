<script>
  import axios from "axios";

  export let amount;
  let rate;
  const format = new Intl.NumberFormat('en-US', { style: "currency", maximumSignificantDigits: 5, currency: "USD", notation: "compact" });
  $: usd_amount = format.format(amount * rate);

  async function load() {
    const resp = await axios.get("https://api.alternative.me/v2/ticker/bitcoin/");
    rate = resp.data.data["1"].quotes.USD.price / 100000000;
  }
</script>

<span {...$$restProps}>
≈{#await load() then}
{usd_amount}
{/await}
</span>

<style>
span {
  font-size: 12px;
}
</style>
