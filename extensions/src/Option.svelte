<script>
	import { createEventDispatcher } from 'svelte';
  import Slider from "./Slider.svelte";
  import Input from "../../frontend/src/lib/Input.svelte";

  export let key;
  export let option;

  const dispatch = createEventDispatcher();

  function reset() {
    option.value = option.default;
    dispatch('change');
  }
</script>

<div class="flex-column width-full">
  <div class="label flex-row align-center width-full gap-8">
    <span>{option.description || key}</span>
    {#if option.default}
      <span class="action reset" on:click={reset} title="Reset to default">⟲</span>
    {:else}
      <span class="action remove" on:click={() => dispatch("remove")} title="Remove">🗑</span>
    {/if}
  </div>
  {#if !option.type || option.type === 'text'}
  <input bind:value={option.value} on:change type=text />
  {:else if option.type === 'number'}
  <Input bind:value={option.value} on:change type=number suffix={option.suffix} />
  {:else if option.type === 'checkbox'}
  <Slider bind:value={option.value} on:change />
  {/if}
</div>

<style>
.label {
  font-weight: 400;
  font-size: 16px;
  margin-bottom: 12px;
}
.remove {
  font-size: 10px;
}
.reset {
  font-size: 18px;
}
span.action {
  cursor: pointer;
}
input {
  width: 100%;
  background: #F8F8F8;
  border: 1px solid #E7E7E7;
  border-radius: 8px;
}
input[type="text"] {
  padding: 18px 22px 18px 22px;
}
</style>
