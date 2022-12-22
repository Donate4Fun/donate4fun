<script>
  import ModalPopup from "$lib/ModalPopup.svelte";
  import { analytics } from "$lib/analytics.js";

  export let show;

  function track(event) {
    return () => analytics.track(event);
  }
</script>

<ModalPopup bind:show={show} --padding="16px 16px 24px 36px">
  <h1>Choose your browser</h1>
  <div class="addon-list">
    <a on:click={track("click-chrome-extension")} class="addon-item" target=_blank href="https://chrome.google.com/webstore/detail/donate4fun/acckcppgcafhbdledejfiiaomafpjmgc">
      <img alt=chrome-icon src="/static/chrome.svg">
      <div class="text">
        Google Chrome or any compatible (Edge, Opera, etc.)
      </div>
    </a>
    <a on:click={track("click-firefox-extension")} class="addon-item" target=_blank href="https://addons.mozilla.org/en-US/firefox/addon/donate4fun/">
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
