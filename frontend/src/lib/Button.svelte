<button {...$$restProps} on:click>
  <slot />
</button>

<style>
button {
  background: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
  font-weight: 700;
  font-size: 16px;
  line-height: 19px;
  color: black;
  padding: 5px 20px;
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
button.white {
  border: 1px solid #000000;
  background: white;
}
button.grey {
  background: #E9E9E9;
}
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
button:disabled {
  opacity: 0.5;
}
button:hover:enabled {
  box-shadow: 0px 8px 20px rgba(185, 192, 204, 0.6);
}
</style>
