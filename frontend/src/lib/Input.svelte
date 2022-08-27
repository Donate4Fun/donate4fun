<script>
  import Error from "../lib/Error.svelte";

  export let value = "";
  export let error = null;
  export let suffix = null;
  export let logo = null;

  function handleInput(e) {
    value = e.target.value;
  }
</script>

<div class=root>
  <div class="wrapper">
    <input value={value} {...$$restProps} class:error="{error !== null}" class:logo={logo !== null}  on:input={handleInput} style:background-image={logo} on:change >
    {#if suffix}
    <div class="suffix">{suffix}</div>
    {/if}
  </div>
  <Error bind:message={error} class="error" />
</div>

<style>
div {
  position: relative;
}
.wrapper {
  display: flex;
  align-items: center;
  background-color: #F8F8F8;
  border: 1px solid #E7E7E7;
  border-radius: 100px;
  padding-left: 24px;
  padding-right: 24px;
  color: #004EE7;
}
input {
  box-sizing: border-box;
  height: 40px;
  border: none;
  background: transparent;

  font-size: 16px;
  line-height: 24px;

  /* identical to box height, or 150% */
  letter-spacing: 0.02em;

  color: #004EE7;
  outline: none;
  width: 100%;
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
input:placeholder-shown {
  color: unset !important;
}
input.error,input:invalid {
  color: #FF4B4B;
}
input.logo {
  background-repeat: no-repeat;
  background-position: 0px 10px;
  padding-left: 45px !important;
}
.wrapper:focus-visible {
  border: 1px solid rgba(0, 78, 231, 0.3);
  filter: drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.25));
}
.root > :global(.error) {
  position: absolute;
  left: 27px;
  top: 40px;
}
.suffix {
  padding-right: 0px;
  opacity: 60%;
}
</style>
