<script>
  import { Link } from "svelte-navigator";
  import Logo from "../lib/Logo.svelte";
  import Social from "../lib/Social.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Loading from "../lib/Loading.svelte";
  import Button from "../lib/Button.svelte";
  import WalletLogin from "../lib/WalletLogin.svelte";
  import {me} from "../lib/session.js";

</script>

<header {...$$restProps}>
  <div class="logo">
    <Link to="/" style="text-decoration: none;">
      <Logo />
    </Link>
  </div>
  <Social class="onlylarge" />
  <div class="right">
    {#await me.init()}
      <Loading/>
    {:then}
      <WalletLogin class="connect" />
      <Userpic user={$me.donator} class="userpic" />
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
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 249, 255, 0.8);
  backdrop-filter: blur(12px);
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
