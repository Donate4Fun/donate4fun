<script>
  import { readable } from "svelte/store";
  import ExtensionPopup from "$lib/ExtensionPopup.svelte";
  import WalletPopup from "$lib/WalletPopup.svelte";
  import LandingStep from "$lib/LandingStep.svelte";
  import { weblnPresent, extensionPresent } from "$lib/utils.js";
  import { analytics } from "$lib/analytics.js";

  let extensionPopupShown = false;
  let walletPopupShown = false;

  function showExtensionPopup() {
    analytics.track('show-extension-popup-from-steps');
    extensionPopupShown = true;
  }
</script>

<ExtensionPopup bind:show={extensionPopupShown} />
<WalletPopup bind:show={walletPopupShown} />

<div class="steps">
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <div on:click={showExtensionPopup} class="step narrow">
    <LandingStep number=1 done={$extensionPresent} doneText="Already installed">
      <img slot=image alt="D" src="/static/extensions.svg">
      <div slot=text>
        <p>Get Donate4.Fun</p>
        <p>browser extension</p>
      </div>
    </LandingStep>
  </div>
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <div on:click={() => walletPopupShown = true} class="step narrow">
    <LandingStep number=2 done={$weblnPresent} doneText="Already installed">
      <img slot=image src="/static/wallet.svg" alt="wallet">
      <div slot=text>
        <p>Get a Lightning Wallet</p>
        <p>if you don’t have it yet</p>
        <p>And fulfill with satoshis</p>
      </div>
    </LandingStep>
  </div>
  <a href="https://youtube.com" target=_blank class="step wide">
    <LandingStep number=3>
      <img slot=image alt="browser-extension" src="/static/extension-popup.png" height=188>
      <div slot=text>
        <p>Go to YouTube and click a ⚡ icon under video or open Donate4fun Google Extension to donate</p>
      </div>
    </LandingStep>
  </a>
</div>

<style>
@media (min-width: 641px) {
  .step.narrow {
    width: 340px;
  }
  .step.wide {
    width: 426px;
  }
}
@media (max-width: 640px) {
  .step {
    width: 328px;
  }
}
.step {
  height: 450px;
  color: var(--color);
  font-weight: 500;
  cursor: pointer;
}
.step div {
  text-align: center;
}
.step.wide p {
  max-width: 308px;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 22px;
}
</style>
