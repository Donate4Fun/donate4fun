<script>
  import Logo from "../lib/Logo.svelte";
  import Social from "../lib/Social.svelte";
  import Userpic from "../lib/Userpic.svelte";
  import Loading from "../lib/Loading.svelte";
  import {me} from "../lib/session.js";
</script>

<header>
  <Logo/>
  <div class="right">
    <Social class="onlylarge" />
    {#await me.init()}
    <Loading/>
    {:then}
    <Userpic {...$me.donator}/>
    {/await}
  </div>
</header>

<style>
header {
  display: flex;
  place-content: space-between;
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
</style>
