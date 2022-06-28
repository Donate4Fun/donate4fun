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
  const amountMin = 10;
  const amountMax = 1000000;

  const alexsc2_channel = "https://www.youtube.com/watch?v=dcjJY0-Aig0";
  const mytest_channel = "https://www.youtube.com/channel/UCk2OzObixhe_mbMfMQGLuJw";

  export let amount = 10;
  export let target = mytest_channel;
  export let message = "You are the best!";
  let error = null;
  let spin = false;

  $: isValid = amount >= amountMin && target;
  $: amountError = (() => {
    if (amount < amountMin)
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
      const data = err.response.data;
      if (data.status === 'error') {
        error = data.error;
      } else {
        error = JSON.stringify(data);
      }
    }
    spin = false;
  }
</script>

<Section class="donate">
  <h1><img src="coin.png"><span>Donate</span></h1>
  <form on:submit|preventDefault={donate}>
    <div>I want to donate <Input class="amount" type="number" placeholder="minimum: 10 000 satoshi" bind:value={amount} bind:error={amountError}/><FiatAmount bind:amount={amount} />
    </div>
    <div>
      To <Input class="url" type="text" placeholder="YouTube channel or video URL" bind:value={target} bind:error={error} />
      <Button class="submit" type=submit disabled={!isValid}>
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
  width: 718px;
  height: 265px;
  padding: 36px 36px 40px 36px;
}
@media only screen and (max-width: 1280px) {
  :global(.donate) {
    width: 100%;
    height: 413px;
    padding: 20px 36px 20px 24px;
  }
}
form {
  display: flex;
  flex-direction: column;
  gap: 36px;
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
@media only screen and (max-width: 1280px) {
  form > div {
    flex-direction: column;
  }
}
form :global(.amount) {
  width: 299px;
  margin-left: 16px;
  margin-right: 20px;
}
form :global(.url) {
  width: 377px;
  margin-left: 17px;
  margin-right: 26px;
  background-image: url(youtube.svg);
  background-repeat: no-repeat;
  background-position: 24px 10px;
  padding-left: 65px !important;
}
form :global(.submit) {
  width: 204px;
}
form :global(.spinner) {
  left: -30px;
}
p {
  display: flex;
  align-items: center;
  white-space: nowrap;
}
</style>
