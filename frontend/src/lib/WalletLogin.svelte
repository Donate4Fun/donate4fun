<script>
  import {me} from "../lib/session.js";
  import Button from "../lib/Button.svelte";
  import {resolve} from "../lib/utils.js";

  export let target = null;
</script>

{#if $me.donator.lnauth_pubkey}
  <Button {...$$restProps} link={resolve('/login')} --padding="11px 45px" --background-image="linear-gradient(90deg, #66E4FF 0%, #F68EFF 100%)">
    <span class="ellipsis">@{$me.donator.lnauth_pubkey}</span>
  </Button>
  {:else}
  <Button {...$$restProps} link={resolve('/login')} target={target}>
    Connect Wallet
  </Button>
{/if}
