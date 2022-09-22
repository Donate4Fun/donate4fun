<script>
  import {createEventDispatcher} from "svelte";
  import Button from "../../frontend/src/lib/Button.svelte";
  import {webOrigin} from "../../frontend/src/lib/utils.js";
  import {me} from "../../frontend/src/lib/session.js";

  const dispatch = createEventDispatcher();
  export let neededAmount;
</script>

<section class="popup flex-column">
  <Button
    on:click={() => dispatch("close")}
    --width=90px
    --padding="6.5px 26px"
    --font-size=16px
    --font-weight=500
    class=grey
  >Close</Button>
  <div>
    <p 
      style="
        grid-row: text;
        font-size: 20px;
        text-align: center;
        line-height: 26px;
      "
      class=message
    >You haven't enought sats and WebLN-enabled wallet is not available. You may either 
    </p>
    <Button
      --height=100%
      style="
        grid-row: download;
      "
      class=light
      target=_blank
      link="{$webOrigin}/install-webln-wallet"
    >Get WebLN-enabled wallet</Button>
    <p style="
      grid-row: text-or;
      font-size: 16px;
      text-align: center;
    ">OR</p>
    <Button
      --height=100%
      target=_blank
      link="{$webOrigin}/fulfill/{$me.donator.id}?amount={neededAmount + 1000}"
      class=white
      style="
        grid-row: fulfill;
      "
    >Fulfill your balance</Button>
  </div>
</section>

<style>
section {
  visibility: visible;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(14.5px);
  gap: 77px;
  padding: 28px;
}
div {
  display: grid;
  grid-template-rows: [text] 78px 42px [download] 72px 25px [text-or] 19px 19px [fulfill] 72px;
}
</style>
