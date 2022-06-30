<script>
  import Logo from "../lib/Logo.svelte";
  import Social from "../lib/Social.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Loading from "../lib/Loading.svelte";
  import Button from "../lib/Button.svelte";
  import {me} from "../lib/session.js";
</script>

<header {...$$restProps}>
  <Logo/>
  <Social class="onlylarge" />
  <div class="right">
    <Button class="connect">Connect Wallet</Button>
    {#await me.init()}
    <Loading/>
    {:then}
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
}
@media only screen and (max-width: 1280px) {
  :global(.onlylarge) {
    display: none;
  }
}
.right {
  display: flex;
  align-items: center;
  gap: 1em;
}
.right :global(.connect) {
  width: 204px;
}
.right :global(.userpic img) {
  width: 56px;
}
</style>
