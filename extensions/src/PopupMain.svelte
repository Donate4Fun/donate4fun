<script>
  import Button from "$lib/Button.svelte";
  import NumberedItem from "$lib/NumberedItem.svelte";
</script>

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
  <!--
  <h1>Supported services</h1>
  <ul class="flex-column width-full gap-8">
    <li class="block font-20">
      <a href="https://youtube.com" target=_blank class="flex-row align-center gap-8">
        <img src="youtube.svg" width=40 alt="youtube logo">
        YouTube
      </a>
    </li>
    <li class="italic block font-15">
      More coming soon
    </li>
  </ul>
  -->
</section>

<style>
.services {
  display: grid;
  grid-template: repeat(2, 1fr) / repeat(2, 1fr);
}
</style>
