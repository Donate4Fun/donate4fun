<script>
	import { createEventDispatcher } from 'svelte';
  import Slider from "./Slider.svelte";
  import Input from "../../frontend/src/lib/Input.svelte";

  export let option;

  const dispatch = createEventDispatcher();

  function reset() {
    option.value = option.default;
    dispatch('change');
  }
</script>

<div>
  <label for={option.name}><span>{option.description}</span><span class=reset on:click={reset} title="Reset to default">⟲</span></label>
  {#if option.type === 'text'}
  <input bind:value={option.value} on:change type=text name={option.name} />
  {:else if option.type === 'number'}
  <Input bind:value={option.value} on:change type=number suffix={option.suffix} />
  {:else if option.type === 'checkbox'}
  <Slider bind:value={option.value} on:change name={option.name} />
  {/if}
</div>

<style>
div {
  display: flex;
  flex-direction: column;
  width: 100%;
}
label {
  width: 100%;
  font-family: 'Inter';
  font-weight: 400;
  font-size: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
span.reset {
  cursor: pointer;
  font-size: 18px;
}
input {
  box-sizing: border-box;
  width: 100%;
  background: #F8F8F8;
  border: 1px solid #E7E7E7;
  border-radius: 8px;
}
input[type="text"] {
  padding: 18px 22px 18px 22px;
}
</style>
