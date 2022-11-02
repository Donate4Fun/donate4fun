<script>
  import ModalPopup from "$lib/ModalPopup.svelte";
  import Wallets from "$lib/Wallets.svelte";

  export let show;
</script>

<ModalPopup bind:show={show}>
  <h1>Choose a Bitcoin Lightning wallet</h1>
  <Wallets />
</ModalPopup>

<style>
h1 {
  font-weight: 700;
  font-size: 24px;
  line-height: 30px;
  text-align: left;
}
</style>
