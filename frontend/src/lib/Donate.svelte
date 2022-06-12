<script>
  import axios from "axios";
  import { createEventDispatcher } from 'svelte';
  import { navigate } from "svelte-routing";
  import Error from "../lib/Error.svelte";
  import Section from "../lib/Section.svelte";
  import Input from "../lib/Input.svelte";
  import Button from "../lib/Button.svelte";
  import Invoice from "../lib/Invoice.svelte";
  import Spinner from "../lib/Spinner.svelte";

	const dispatch = createEventDispatcher();
  const amountMin = 10;

  let amount = 10;
  //let target = "";
  let target = "https://www.youtube.com/watch?v=dcjJY0-Aig0"; // tmp for dev
  let message = "You are the best!";
  let error = null;
  let spin = false;
  let invoice = null;
  let donation = null;

  $: isValid = amount >= amountMin && target;

  async function donate(e) {
    spin = true;
    try {
      const resp = await axios.post('/api/v1/donate', {
          amount: amount,
          target: target,
          message: message
      });
      invoice=resp.data;
    } catch (err) {
      console.log(err);
      const data = err.response.data;
      if (typeof myVar === 'string') {
        error = data;
      } else {
        error = data.message || data.detail[0].msg;
      }
    }
    spin = false;
  }
  function cancel() {
    console.log("invoice cancel");
    invoice = null;
  }
  function close() {
    console.log("donate close");
    donation = null;
  }
  function paid(new_donation) {
    console.log("paid", new_donation);
    invoice = null;
    donation = new_donation;
  }
</script>

<Section>
  {#if invoice}
  <Invoice invoice={invoice} on:cancel={cancel} on:paid={paid} />
  {:else if donation}
  <Donation {...donation} on:close={close} />
  {:else}
  <h1>Donate</h1>
  <Error bind:message={error} />
  <form on:submit|preventDefault={donate}>
    <p>I want to donate <Input type="number" placeholder="minimum: 10 000 satoshi" bind:value={amount} /> satoshis</p>
    <p>
      to <Input type="text" placeholder="YouTube channel or video URL" bind:value={target} />
      <Button type=submit disabled={!isValid}>
        {#if spin}
        <Spinner size=20px width=3px/>
        {/if}
        &nbsp;&nbsp;Donate
      </Button>
    </p>
  </form>
  {/if}
</Section>

<style>
p,h1 {
  margin: inherit;
}
p {
  display: flex;
  align-items: center;
  white-space: nowrap;
}
</style>
