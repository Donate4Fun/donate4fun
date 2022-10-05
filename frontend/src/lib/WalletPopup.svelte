<script>
  import ModalPopup from "$lib/ModalPopup.svelte";

  export let show;
</script>

<ModalPopup bind:show={show}>
  <h1>Choose a Bitcoin Lightning wallet</h1>
  <div class="wallet-list">
    <a class="wallet-item" target=_blank href="https://getalby.com">
      <img alt=alby-icon src="/static/alby.svg">
      <div class="text">Alby browser wallet</div>
    </a>
    <a class="wallet-item" target=_blank href="https://blixtwallet.github.io">
      <img alt=blixt-icon src="/static/blixt-wallet-icon.png">
      <div class="text">Blixt mobile wallet</div>
    </a>
  </div>
</ModalPopup>

<style>
h1 {
  font-weight: 700;
  font-size: 24px;
  line-height: 30px;
  text-align: left;
}
.wallet-item img {
  height: 32px;
  width: 32px;
}
.wallet-list {
  display: flex;
  flex-direction: column;
}
.wallet-item {
  display: flex;
  gap: 16px;
  align-items: center;
  height: 72px;
}
.wallet-item .text {
  font-weight: 600;
  font-size: 16px;
  line-height: 22px;
}
</style>
