<script>
  import {useResolve} from "svelte-navigator";
  import Logo from "../lib/Logo.svelte";
  import Social from "../lib/Social.svelte";
  import Extensions from "../lib/Extensions.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Loading from "../lib/Loading.svelte";
  import Button from "../lib/Button.svelte";
  import {me} from "../lib/session.js";

  const resolve = useResolve();
</script>

<header {...$$restProps}>
  <div class="logo"><Logo /></div>
  <Social class="onlylarge" />
  <Extensions class="onlylarge" />
  <div class="right">
    {#await me.init()}
    <Loading/>
    {:then}
      {#if $me.donator.lnauth_pubkey}
      <Button class="connect connected" link={resolve('/login')}>
        <span>@{$me.donator.lnauth_pubkey}</span>
      </Button>
      {:else}
      <Button class="connect" link={resolve('/login')}>
        Connect Wallet
      </Button>
      {/if}
    <Userpic {...$me.donator} class="userpic" />
    {/await}
  </div>
</header>

<style>
header {
  display: flex;
  align-items: center;
  place-content: space-between;
  width: 100%;
  padding: 23px 40px 23px 40px;
  box-sizing: border-box;
  font-size: 15px;
}
.right :global(.connected) {
  padding: 0 45px;
  background: linear-gradient(90deg, #66E4FF 0%, #F68EFF 100%);
}
header span {
  text-overflow: ellipsis;
  overflow: hidden;
}
@media (max-width: 1280px) {
  :global(.onlylarge) {
    display: none;
  }
}
@media (max-width: 640px) {
  .right :global(.connect) {
    width: 158px;
    padding: 10px;
  }
  header {
    padding-left: 12px;
    padding-right: 20px;
  }
}
@media (min-width: 641px) {
  .right :global(.connect) {
    width: 204px;
  }
}
.right {
  display: flex;
  align-items: center;
  gap: 25px;
}
.right :global(.userpic img) {
  width: 56px;
}
</style>
