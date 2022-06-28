<script>
  import Error from "../lib/Error.svelte";

  export let value = "";
  export let error = null;
</script>

<div>
  <input bind:value class:witherror="{error !== null}" {...$$restProps}>
  <Error bind:message={error} class="error" />
</div>

<style>
div {
  position: relative;
}
input {
  background-color: #F8F8F8;
  border: 1px solid #E7E7E7;
  border-radius: 100px;
  box-sizing: border-box;
  height: 40px;

  font-size: 16px;
  line-height: 24px;

  /* identical to box height, or 150% */
  letter-spacing: 0.02em;

  color: #004EE7;
  padding-left: 24px;
  padding-right: 24px;
}
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}
input.witherror {
  color: #FF4B4B;
}
input:focus-visible {
  border: 1px solid rgba(0, 78, 231, 0.3);
  filter: drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.25));
  outline: none;
}
:global(.error) {
  position: absolute;
  left: 42px;
  top: 40px;
}
</style>
