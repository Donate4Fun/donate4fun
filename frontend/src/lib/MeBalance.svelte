<script>
  import Amount from "../lib/Amount.svelte";
  import FiatAmount from "../lib/FiatAmount.svelte";
  import Button from "../lib/Button.svelte";
  import {me} from "../lib/session.js";
  import {resolve, isExtension} from "../lib/utils.js";
</script>

<main>
  <div style="grid-row: sats;" class="amount flex-row justify-center">
    <Amount class="font-24 font-weight-700i grid-column-2 text-align-center" amount={$me.donator.balance} />
  </div>
  <FiatAmount
    style="grid-row: fiat; line-height: 16px;"
    class="font-12 font-weight-400 text-align-center" amount={$me.donator.balance} />
  <Button
    style="grid-row: fulfill;"
    target={isExtension ? "_blank" : null}
    link={resolve(`/fulfill/${$me.donator.id}`)}
    class=white
    --padding="10px 41px"
  >Fulfill</Button>
</main>

<style>
main {
  display: grid;
  grid-template-rows: [sats] 29px 12px [fiat] 16px 20px [fulfill] 41px;
}
</style>
