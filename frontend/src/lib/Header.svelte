<script>
  import { Link, link } from "svelte-navigator";
  import Logo from "../lib/Logo.svelte";
  import Social from "../lib/Social.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import Button from "../lib/Button.svelte";
  import WalletLogin from "../lib/WalletLogin.svelte";
  import {me} from "../lib/session.js";
  import { resolve } from "$lib/utils.js";
</script>

<header>
  <div class="logo">
    <Link to="/" style="text-decoration: none;">
      <Logo />
    </Link>
  </div>
  <div class="right">
    <a class="desktop-only" use:link href={resolve("/#roadmap")}>Roadmap</a>
    <a class="desktop-only" use:link href={resolve("/prove/youtube")}>Claim donations</a>
    <div class="connect-button">
      <WalletLogin />
    </div>
    <div class="userpic">
      {#await $me.loaded then}
        <Userpic user={$me.donator} />
      {/await}
    </div>
  </div>
</header>

<style>
header {
  display: flex;
  align-items: center;
  place-content: space-between;
  width: 100%;
  height: 88px;
  box-sizing: border-box;
  font-size: 15px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 249, 255, 0.8);
  backdrop-filter: blur(12px);
}
@media (max-width: 640px) {
  .connect-button {
    width: 158px;
    font-size: 15px;
    line-height: 18px;
    --padding: 11px 22px;
  }
  header {
    padding-left: 18px;
    padding-right: 24px;
  }
  .userpic {
    --width: 48px;
    --size: 48px;
  }
}
@media (min-width: 641px) {
  .connect-button {
    width: 204px;
    --padding: 11px 22px;
  }
  header {
    padding-left: 28px;
    padding-right: 40px;
  }
  .userpic {
    --width: 56px;
    --size: 56px;
  }
}
.right {
  display: flex;
  align-items: center;
  gap: 25px;
  font-weight: 700;
}
.right > a {
  font-size: 15px;
  line-height: 18px;
  text-align: center;
  letter-spacing: 0.01em;
  color: var(--color);
}
</style>
