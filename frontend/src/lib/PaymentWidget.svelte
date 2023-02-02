<script>
  import { tick, createEventDispatcher } from "svelte";
  import { slide } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  import Amount from "$lib/Amount.svelte";
  import AmountSelection from "$lib/AmountSelection.svelte";
  import Invoice from "$lib/Invoice.svelte";
  import api from "$lib/api.js";

  export let target;
  export let paymentRequest = null;

  let amount;
  let donation;
  let showSuccess = false;

  const dispatch = createEventDispatcher();

  async function donate(amount_) {
    // Make a donation
    amount = amount_;
    const response = await api.post('donate', {
      amount: amount,
      ...target,
    });
    donation = response.donation;
    if (donation.paid_at) {
      dispatch('paid');
    } else {
      // If donation is not paid using balance then use Invoice
      paymentRequest = response.payment_request;
    }
  }

  async function paid(event) {
    const donation = event.detail;
    amount = donation.amount;
    paymentRequest = null;
    dispatch('paid');
    // Trigger fadeout
    showSuccess = true;
    await tick();
    showSuccess = false;
  }
</script>

<div class="payment">
  {#if paymentRequest}
    <Amount {amount} />
    <Invoice {donation} {paymentRequest} on:cancel={() => paymentRequest = null} on:paid={paid} />
  {:else if showSuccess}
    <div class="success" out:slide={{duration: 300, delay: 2000, easing: cubicOut}}>
      <div>Paid <Amount {amount} /></div>
      <img src="/static/success.png" alt=success width=120 height=120>
    </div>
  {:else}
    <AmountSelection {donate} />
  {/if}
</div>

<style>
.payment {
  width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.success {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
</style>
