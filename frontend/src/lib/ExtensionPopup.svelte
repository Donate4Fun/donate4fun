<script>
  import ModalPopup from "$lib/ModalPopup.svelte";

  export let show;
</script>

<ModalPopup bind:show={show}>
  <h1>Choose your browser</h1>
  <div class="addon-list">
    <a class="addon-item" target=_blank href="https://chrome.google.com/webstore/detail/donate4fun/acckcppgcafhbdledejfiiaomafpjmgc">
      <img alt=chrome-icon src="/static/chrome.svg">
      <div class="text">
        Google Chrome or any compatible (Edge, Opera, etc.)
      </div>
    </a>
    <a class="addon-item" target=_blank href="https://addons.mozilla.org/en-US/firefox/addon/donate4fun/">
      <img alt=firefox-icon src="/static/firefox.svg">
      <div class="text">
        Firefox
      </div>
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
.addon-list {
  display: flex;
  flex-direction: column;
}
.addon-item {
  display: flex;
  gap: 16px;
  align-items: center;
  height: 72px;
}
.addon-item .text {
  font-weight: 600;
  font-size: 16px;
  line-height: 22px;
}
</style>
