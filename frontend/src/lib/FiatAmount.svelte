<script>
  import { btcUsdRate } from "$lib/ticker.js";

  export let amount;

  const format = new Intl.NumberFormat('en-US', { style: "currency", maximumSignificantDigits: 2, currency: "USD", notation: "compact" });
  $: usd_amount = format.format(amount * $btcUsdRate);
</script>

<span {...$$restProps}>
≈{usd_amount}
</span>

<style>
span {
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.015em;
  font-weight: 400;
}
</style>
