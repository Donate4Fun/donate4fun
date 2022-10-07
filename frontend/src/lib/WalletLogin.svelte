<script>
  import {me} from "../lib/session.js";
  import Button from "../lib/Button.svelte";
  import {resolve} from "../lib/utils.js";

  export let target = null;
</script>

{#await $me.loaded}
  <Button class="grey" --width=100%>...</Button>
{:then}
  {#if $me.donator.lnauth_pubkey}
    <Button link={resolve('/login')} --padding="11px 45px" --width=100% --background-image="linear-gradient(90deg, #66E4FF 0%, #F68EFF 100%)">
      <span class="ellipsis">{$me.shortkey}</span>
    </Button>
  {:else}
    <Button link={resolve('/login')} --width=100% target={target}>
      Connect Wallet
    </Button>
  {/if}
{/await}
