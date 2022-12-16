<script>
  import { link } from "svelte-navigator";

  import LandingSection from "$lib/LandingSection.svelte";
  import Amount from "$lib/Amount.svelte";
  import { youtube_channel_url } from "$lib/utils.js";

  export let donatee;
</script>

<section>
  <LandingSection>
    <a href="/{donatee.type}/{donatee.id}" use:link>
      <img alt="logo" src={donatee.thumbnail_url} width=120 height=120>
      <p class="title ellipsis">{donatee.title}</p>
      <div>
        <p>Got donated</p>
        <Amount amount={donatee.total_donated} />
      </div>
    </a>
  </LandingSection>
</section>

<style>
section {
  min-width: 240px;
  height: 288px;
}
a {
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  font-weight: 500;
  line-height: 24px;
  font-size: 16px;
  color: var(--color);
  text-align: center;
}
img {
  border-radius: 100%;
}
p.title {
  font-size: 20px;
  text-align: center;
  max-width: 100%;
  color: var(--link-color);
}
</style>
