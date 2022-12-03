<script>
  import ServiceLinkButton from "$lib/ServiceLinkButton.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
  import PopupSection from "$extlib/PopupSection.svelte";
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
        <ServiceLinkButton on:click={close} link="https://youtube.com">
          <img alt=youtube src="/static/youtube.svg" class="service-icon">
          <span class="service-name">YouTube</span>
        </ServiceLinkButton>
        <ServiceLinkButton on:click={close} link="https://twitter.com">
          <img alt=twitter src="/static/twitter.svg" class="service-icon">
          <span class="service-name">Twitter</span>
        </ServiceLinkButton>
      </div>
      <div class="services-line">
        <ServiceLinkButton on:click={close} link="https://github.com/orgs/Donate4Fun/projects/1/views/1?filterQuery=label%3Aproviders+">
          <span class="service-name">More soon</span>
        </ServiceLinkButton>
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
