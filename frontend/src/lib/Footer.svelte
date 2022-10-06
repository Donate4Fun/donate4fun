<script>
  import GithubBrand from "svelte-awesome-icons/GithubBrand.svelte";
  import DiscordBrand from "svelte-awesome-icons/DiscordBrand.svelte";
</script>

<footer>
  <div>2022 Donate4Fun<sup>©</sup></div>
  <div class="links">
    <a target=_blank href="https://github.com/donate4Fun/donate4fun"><GithubBrand size=32 color="var(--link-color)" /></a>
    <a target=_blank href="https://discord.gg/pfFRGWZ4TM"><DiscordBrand size=32 color="var(--link-color)" /></a>
    <a target=_blank href="https://donate4fun.notion.site/Donat4-Fun-Roadmap-9fe79f04955b4e6bbac73175efee4351">FAQ</a>
    <a href="/terms">Terms and Privacy Policy</a>
  </div>
</footer>

<style>
footer {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
  font-size: 14px;
  padding: 28px 62px 28px 62px;
}
.links {
  display: flex;
  gap: 2em;
  align-items: center;
}
.links a {
  font-weight: 500;
}
</style>
