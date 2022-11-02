<script>
  import GooglePlayIcon from "$lib/GooglePlayIcon.svelte";
  import AppStoreIcon from "$lib/AppStoreIcon.svelte";
  import ChromeIcon from "$lib/ChromeIcon.svelte";
  import FirefoxIcon from "$lib/FirefoxIcon.svelte";
  import FDroidIcon from "$lib/FDroidIcon.svelte";

  export let browser = true;
  export let mobile = true;
</script>

<div class="wallet-list">
  {#if browser}
    <a class="wallet-item" target=_blank href="https://getalby.com">
      <img alt="alby" src="/static/alby.svg">
      <div class="text">Alby browser wallet</div>
      <a href="https://addons.mozilla.org/en-US/firefox/addon/alby/" target=_blank><FirefoxIcon /></a>
      <a href="https://chrome.google.com/webstore/detail/alby-bitcoin-lightning-wa/iokeahhehimjnekafflcihljlcjccdbe" target=_blank><ChromeIcon /></a>
    </a>
  {/if}
  {#if mobile}
    <a class="wallet-item" target=_blank href="https://blixtwallet.github.io">
      <img alt="blixt" icon src="/static/blixt-wallet-icon.png">
      <div class="text">Blixt mobile wallet</div>
      <a href="https://play.google.com/store/apps/details?id=com.blixtwallet" target=_blank><GooglePlayIcon /></a>
      <a href="https://testflight.apple.com/join/EXvGhRzS" target=_blank><AppStoreIcon /></a>
    </a>
    <a class="wallet-item" target=_blank href="https://sbw.app/">
      <img alt="sbw" icon src="/static/sbw.svg">
      <div class="text">Simple Bitcoin Wallet (Android only)</div>
      <a href="https://play.google.com/store/apps/details?id=com.btcontract.wallet" target=_blank><GooglePlayIcon /></a>
      <a href="https://f-droid.org/repository/browse/?fdid=com.btcontract.wallet" target=_blank><FDroidIcon /></a>
    </a>
    <a class="wallet-item" target=_blank href="https://phoenix.acinq.co/">
      <img alt="phoenix" src="/static/phoenix.svg">
      <div class="text">Phoenix Wallet</div>
      <a href="https://apps.apple.com/us/app/phoenix-wallet/id1544097028" target=_blank><AppStoreIcon /></a>
      <a href="https://play.google.com/store/apps/details?id=fr.acinq.phoenix.mainnet" target=_blank><GooglePlayIcon /></a>
    </a>
  {/if}
</div>

<style>
.wallet-item img {
  height: 32px;
  width: 32px;
  border-radius: 5px;
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
  --icon-size: 24px;
}
.wallet-item .text {
  font-weight: 600;
  font-size: 16px;
  line-height: 22px;
}
</style>
