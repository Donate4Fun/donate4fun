<script>
  import Section from "$lib/Section.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import { me, resetMe } from "$lib/session.js";
</script>

<Section>
  <div class="content">
    <div class="image-and-name">
      {#await $me then me}
        <Userpic clickable={false} user={me.donator} class="userpic" --width=88px/>
        <MeNamePubkey />
      {/await}
    </div>
    <div class="buttons">
      <SocialSigninButton height=48px link="/login?return=/donator/me" type="bolt">Sign in with Lightning</SocialSigninButton>
      <SocialSigninButton height=48px type="youtube">Sign in with YouTube</SocialSigninButton>
      <SocialSigninButton height=48px type="twitter">Sign in with Twitter</SocialSigninButton>
    </div>
  </div>
</Section>

<style>
.content {
  max-width: 640px;
  min-width: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 174px;
  gap: 44px;
}
.image-and-name {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}
.buttons {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 300px;
}
</style>
