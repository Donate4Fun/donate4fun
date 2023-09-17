<script>
  import Input from "$lib/Input.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import AmountButton from "$lib/AmountButton.svelte";
  import { me } from "$lib/session.js";
  import { toText } from "$lib/utils.js";

  export let amount = 100;
  export let donate;

  const amounts = [100, 1000, 10000];
  const amountMin = 10;
  const amountMax = 1000000;
  $: valid = amount >= amountMin && amount <= amountMax;
</script>

<div class="container">
  <div class="amount-buttons">
  {#each amounts as amount_}
    <AmountButton
      on:click={() => amount = amount_}
      --padding="8px"
      selected={amount_ === amount}
    >{toText(amount_)} ⚡</AmountButton>
  {/each}
  </div>
  <div class="amount-input">
    <div class="flex-grow input">
      <Input type=number bind:value={amount} min={amountMin} max={amountMax} suffix=sats required />
    </div>
    <FiatAmount bind:amount={amount} />
  </div>
  {#await $me then me}
    {#if amount <= me.donator.balance}
      <Button --width=100% on:click={() => donate(amount)} --padding="9px" disabled={!valid}>Donate</Button>
    {:else}
      <Button --width=100% on:click={() => donate(amount)} --padding="9px" disabled={!valid}>Donate with WebLN</Button>
    {/if}
  {/await}
</div>

<style>
.container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.input {
  font-weight: 400;
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.015em;
}
.amount-buttons {
  display: flex;
  gap: 16px;

  font-size: 14px;
  line-height: 20px;
}
.amount-input {
  display: flex;
  align-items: center;
  gap: 20px;

  font-size: 14px;
  line-height: 24px;
}
</style>
