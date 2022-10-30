<script>
  import { link } from "svelte-navigator";
  import GithubBrand from "svelte-awesome-icons/GithubBrand.svelte";
  import DiscordBrand from "svelte-awesome-icons/DiscordBrand.svelte";
  import TwitterBrand from "svelte-awesome-icons/TwitterBrand.svelte";

  const version = import.meta.env.VITE_VERSION;
</script>

<footer>
  <div title={version}>2022 Donate4Fun<sup>©</sup></div>
  <div class="links">
    <a target=_blank href="https://twitter.com/donate4_fun"><TwitterBrand size=32 color="var(--link-color)" /></a>
    <a target=_blank href="https://github.com/donate4Fun/donate4fun"><GithubBrand size=32 color="var(--link-color)" /></a>
    <a target=_blank href="https://discord.gg/pfFRGWZ4TM"><DiscordBrand size=32 color="var(--link-color)" /></a>
    <a use:link href="/terms">Terms</a>
    <a use:link href="/privacy">Privacy</a>
  </div>
</footer>

<style>
footer {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  width: 100%;
}
.links {
  display: flex;
  align-items: center;
}
.links a {
  font-weight: 500;
}
@media (max-width: 640px) {
  footer {
    padding: 28px 1em;
  }
  .links {
    gap: 0.5em;
    justify-content: space-evenly;
    flex-grow: 1;
  }
}
@media (min-width: 641px) {
  footer {
    padding: 28px 62px;
  }
  .links {
    gap: 2em;
  }
}

</style>
