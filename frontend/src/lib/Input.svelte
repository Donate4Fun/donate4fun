<script>
  export let value = "";
</script>

<input bind:value {...$$restProps}>

<style>
input {
  background: #F8F8F8;
  border: 1px solid #E7E7E7;
  border-radius: 100px;
  box-sizing: border-box;
  height: 40px;
  width: 100%;
  margin: 0 10px;

  font-size: 16px;
  line-height: 24px;

  /* identical to box height, or 150% */
  letter-spacing: 0.02em;

  color: #004EE7;
  padding: 5px 20px;
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
</style>
