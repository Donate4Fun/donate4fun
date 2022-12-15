<script>
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import WhiteButton from "$lib/WhiteButton.svelte";
  import {me} from "$lib/session.js";
  import {resolve, isExtension} from "$lib/utils.js";

  const withdrawMin = 100;
</script>

<main>
  {#await $me then me}
    <div style="grid-row: sats;" class="amount">
      <Amount amount={me.donator.balance} />
    </div>
    <FiatAmount
      style="grid-row: fiat; line-height: 16px;"
      class="font-12 font-weight-400 text-align-center" amount={me.donator.balance} />
    <div class="buttons">
      <WhiteButton
        target={isExtension ? "_blank" : null}
        link={resolve("/fulfill/me")}
        --width=125px
      >Fulfill</WhiteButton>
      <WhiteButton
        title="Minimum withdrawal amount is {withdrawMin} sats"
        disabled={me.donator.balance <= withdrawMin}
        target={isExtension ? "_blank" : null}
        link={resolve("/me/withdraw")}
        --width=125px
      >Withdraw</WhiteButton>
    </div>
  {/await}
</main>

<style>
main {
  display: grid;
  grid-template-rows: [sats] 29px 12px [fiat] 16px 20px [fulfill] 41px;
}
.amount {
  display: flex;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  grid-template-columns: repeat(2, 1fr);
}
.buttons {
  grid-row: fulfill;
  display: flex;
  justify-content: center;
  gap: 20px;
  height: 40px;
}
</style>
