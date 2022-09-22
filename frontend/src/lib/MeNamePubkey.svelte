<script>
  import {me} from "../lib/session.js";
</script>

<div class="flex-column align-center justify-center gap-10">
  <p class="font-15 margin-0">{$me.donator.name}</p>
  {#if $me.donator.lnauth_pubkey}
    <p class="flex-row gap-6 font-12 font-weight-300 margin-0">Connected wallet: <span class="ellipsis font-weight-600">{$me.shortkey}</span></p>
  {/if}
</div>
