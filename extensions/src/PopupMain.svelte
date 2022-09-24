<script>
  import { useNavigate } from "svelte-navigator";
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import {getCurrentTab, contentScript, isTest} from "./common.js";

	const navigate = useNavigate();

  async function load() {
    console.log("load main", window.location.hash);
    let showYoutube;
    if (isTest()) {
      showYoutube = true;
    } else {
      const tab = await getCurrentTab();
      showYoutube = tab?.url?.match('^https\:\/\/(www\.)?youtube\.com') && await contentScript.isVideoLoaded();
    }
    if (showYoutube)
      navigate("youtube");
  }
</script>

{#await load() then}
<section class="flex-column align-center">
  <NumberedItem number=1>
    <span>
      Open video channel or author you want to donate 
    </span>
  </NumberedItem>
  <div class="services">
    <Button><img alt=youtube src="/static/youtube.svg">YouTube</Button>
  </div>
  <NumberedItem number=2>
    <span>
      Click a ⚡ icon under video or use this popup
    </span>
  </NumberedItem>
</section>
{/await}

<style>
.services {
  display: grid;
  grid-template: repeat(2, 1fr) / repeat(2, 1fr);
}
</style>
