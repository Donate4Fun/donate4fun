<script>
  import Spinner from "../lib/Spinner.svelte";

  export let loading = false;
</script>

<button {...$$restProps} on:click>
{#if loading}
  <Spinner color=white />
{/if}
  <div>
    <slot />
  </div>
</button>

<style>
button > div {
  
}
button {
  background: linear-gradient(90deg, #00A3FF 0%, #7000FF 100%);
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
  color: #FFFFFF;
  padding: 5px 20px;
  margin-left: 10px;
  cursor: pointer;
  height: 40px;

  border: 1px solid #E7E7E7;
  border-radius: 100px;

  /* identical to box height, or 150% */
  letter-spacing: 0.02em;

  display: flex;
  align-items: center;
  justify-content: center;
}
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
button:disabled {
  background: grey;
}
</style>
