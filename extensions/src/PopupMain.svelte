<script>
  import { useNavigate } from "svelte-navigator";
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import PopupSection from "./PopupSection.svelte";
  import {getCurrentTab, connectToPage} from "./common.js";

	const navigate = useNavigate();

  async function load() {
    console.log("load main", window.location.hash);
    const tab = await getCurrentTab();
    if (!tab?.url?.match('^https\:\/\/(www\.)?youtube\.com'))
      return;
    try {
      const contentScript = await connectToPage();
      const showYoutube =  await contentScript.isVideoLoaded();
      if (showYoutube)
        navigate("youtube");
    } catch (error) {
      console.log("error connecting to tab", error);
    }
  }
</script>

<PopupSection --align-items=start>
  {#await load() then}
    <NumberedItem number=1>
      <span>
        Open video channel or author you want to donate
      </span>
    </NumberedItem>
    <div class="services">
      <Button class="blue" link="https://youtube.com" target="_blank"><img alt=youtube src="/static/youtube.svg" class="service-icon"><span class="service-name">YouTube</span></Button>
      <Button class="blue" link="https://github.com/orgs/Donate4Fun/projects/1/views/1?filterQuery=label%3Aproviders+" target="_blank"><span class="service-name">More soon</span></Button>
    </div>
    <NumberedItem number=2>
      <span>
        Click a ⚡ icon under video or use this popup
      </span>
    </NumberedItem>
  {/await}
</PopupSection>

<style>
.services {
  display: grid;
  grid-template: repeat(1, 1fr) / repeat(2, 1fr);
  gap: 20px 18px;
  margin-top: 18px;
  margin-bottom: 40px;
  margin-right: 43px;
}
.service-icon {
  margin-right: 16px;
  height: 100%;
}
.service-name {
  line-height: 25px;
}
</style>
