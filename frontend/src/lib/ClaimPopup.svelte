<script>
  import { link } from "svelte-navigator";
  import ModalPopup from "$lib/ModalPopup.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";

  export let show;
</script>

<ModalPopup bind:show={show} --padding="16px 16px 24px 36px">
  <div class="container">
    <h1>Where did you receive a donation?</h1>
    <div class="list">
      <SocialSigninButton type="youtube">Claim from YouTube</SocialSigninButton>
      <SocialSigninButton type="twitter">Claim from Twitter</SocialSigninButton>
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
  gap: 32px;
}
</style>
