<script>
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import PopupSection from "./PopupSection.svelte";
  import cLog from "$lib/log.js";

  function close() {
    window.close();
  }
</script>

<PopupSection>
  <div class="content">
    <div class="services">
      <NumberedItem number=1>
        <span>
          Choose a service where you want to donate
        </span>
      </NumberedItem>
      <div class="services-line">
        <Button class="blue" on:click={close} link="https://youtube.com" target="_blank"><img alt=youtube src="/static/youtube.svg" class="service-icon"><span class="service-name">YouTube</span></Button>
        <Button class="blue" on:click={close} link="https://github.com/orgs/Donate4Fun/projects/1/views/1?filterQuery=label%3Aproviders+" target="_blank"><span class="service-name">More soon</span></Button>
      </div>
    </div>
    <NumberedItem number=2>
      <span>
        Click a ⚡ icon under video or use this popup
      </span>
    </NumberedItem>
  </div>
</PopupSection>

<style>
.content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}
.services {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.services-line {
  display: flex;
  gap: 16px;
}
.service-icon {
  margin-right: 16px;
  height: 24px;
  width: 30px;
}
.service-name {
  line-height: 25px;
}
</style>
