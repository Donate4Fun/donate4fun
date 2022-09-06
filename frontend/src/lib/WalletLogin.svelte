<script>
  import {me} from "../lib/session.js";
  import Button from "../lib/Button.svelte";
  import {resolve} from "../lib/utils.js";

  export let target = null;
</script>

{#if $me.donator.lnauth_pubkey}
<Button class="connect connected" link={resolve('/login')}>
  <span class="ellipsis">@{$me.donator.lnauth_pubkey}</span>
</Button>
{:else}
<Button class="connect" link={resolve('/login')} target={target}>
  Connect Wallet
</Button>
{/if}
