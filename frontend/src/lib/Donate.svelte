<script>
  import { createEventDispatcher } from 'svelte';
  import { navigate } from "svelte-navigator";

  import api from "../lib/api.js";
  import Error from "../lib/Error.svelte";
  import Section from "../lib/Section.svelte";
  import Input from "../lib/Input.svelte";
  import Button from "../lib/Button.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import FiatAmount from "../lib/FiatAmount.svelte";

	const dispatch = createEventDispatcher();
  const amountMin = 100;
  const amountMax = 1000000;
  const fmt = new Intl.NumberFormat('en-US', { maximumSignificantDigits: 5, notation: "compact" });

  export let amount = 1000;
  export let target;
  export let message = "You are the best!";
  let error = null;
  let spin = false;

  $: isValid = amount >= amountMin && target;
  $: amountError = (() => {
    if (amount === "")
      return `enter the whole number`;
    else if (amount < amountMin)
      return `minimum: ${amountMin} sats`;
    else if (amount > amountMax)
      return `maximum: ${amountMax} sats`;
    else
      return null;
  })();

  async function donate(e) {
    spin = true;
    try {
      const response = await api.post('donate', {
          amount: amount,
          target: target,
          message: message
      });
      navigate(`/donation/${response.donation.id}`, {state: response});
    } catch (err) {
      console.log(err);
      if (err.status === 'error') {
        error = err.error;
      } else {
        error = JSON.stringify(err);
      }
    }
    spin = false;
  }
</script>

<Section class="donate">
  <h1><img src="/static/coin.png" alt="coin"><span>Donate</span></h1>
  <form on:submit|preventDefault={donate}>
    <div class="first-line">
      <span class="i-want">I want to donate</span>
      <div class="amount"><Input type=number placeholder="Enter amount" bind:value={amount} min={amountMin} max={amountMax} bind:error={amountError} suffix=sats required /></div>
      <FiatAmount bind:amount={amount} class="fiat-amount" />
    </div>
    <div class="second-line">
      <span class=to>To</span>
      <div class="url"><Input type="text" placeholder="Paste YouTube URL" bind:value={target} bind:error={error} logo=url(/static/youtube.svg) required /></div>
      <Button class="submit" type=submit>
        {#if spin}
        <Spinner class="spinner" size=20px width=3px/>
        {/if}
        <span>Donate</span>
      </Button>
    </div>
  </form>
</Section>

<style>
:global(.donate) {
  box-sizing: border-box;
  width: 640px;
  height: 265px;
  padding: 36px 36px 40px 36px;
}
@media only screen and (max-width: 640px) {
  :global(.donate) {
    width: 100%;
    height: 413px;
    padding: 20px 36px 20px 24px;
  }
  form {
    gap: 20px;
  }
  form > div {
    flex-direction: column;
  }
  .first-line .i-want {
    align-self: start;
  }
  .first-line .amount {
    width: 100%;
    margin-top: 16px;
    margin-bottom: 12px;
  }
  .first-line :global(.fiat-amount) {
    align-self: end;
  }
  .second-line .to {
    align-self: start;
  }
  .second-line .url {
    width: 100%;
    margin-top: 16px;
    margin-bottom: 24px;
  }
  .second-line :global(input) {
    width: 100% !important;
    margin: 0 !important;
  }
  .second-line :global(.submit) {
    width: 100%;
  }
}
form {
  display: flex;
  flex-direction: column;
}
@media only screen and (min-width: 641px) {
  form {
    gap: 36px;
  }
}
h1 {
  display: flex;
  margin-top: 0px;
  margin-bottom: 44px;
  align-items: center;
  gap: 12px;
}
h1 > img {
  width: 35px;
  height: 35px;
  filter: drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.25));
  margin-top: -10px;
  margin-bottom: -10px;
}
form > div {
  display: flex;
  align-items: center;
}
.amount {
  width: 299px;
  margin-left: 16px;
  margin-right: 20px;
}
.second-line {
  justify-content: space-between;
}
.second-line .url {
  margin-left: 14px;
  margin-right: 24px;
}
form :global(.submit) {
  width: 180px;
}
form :global(.spinner) {
  left: -30px;
}
</style>
