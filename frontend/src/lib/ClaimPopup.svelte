<script>
  import { link } from "svelte-navigator";
  import ModalPopup from "$lib/ModalPopup.svelte";

  export let show;
</script>

<ModalPopup bind:show={show}>
  <div class="container">
    <h1>Where did you receive a donation?</h1>
    <div class="list">
      <a class="item" use:link on:click={() => show = false} href="/youtube/prove">
        <img alt=youtube src="/static/youtube.svg">
        <div class="text">YouTube</div>
      </a>
      <a class="item" use:link on:click={() => show = false} href="/twitter/prove">
        <img alt=twitter src="/static/twitter.svg">
        <div class="text">Twitter</div>
      </a>
    </div>
  </div>
</ModalPopup>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: start;
  gap: 18px;
}
h1 {
  font-weight: 700;
  font-size: 24px;
  line-height: 30px;
  text-align: left;
}
.list {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}
.item {
  display: flex;
  justify-content: start;
  align-items: center;
  padding: 14px 36px 14px 0px;
  gap: 16px;
}
.item .text {
  font-weight: 600;
  font-size: 16px;
  line-height: 22px;
}
.item img {
  width: 32px;
}
</style>
