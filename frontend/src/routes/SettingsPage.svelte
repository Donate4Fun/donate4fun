<script>
  import { useNavigate } from "svelte-navigator";

  import Section from "$lib/Section.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import Userpic from "$lib/Userpic.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import LinkedItems from "$lib/LinkedItems.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import { me, resetMe, reloadMe } from "$lib/session.js";
  import api from "$lib/api.js";

  const navigate = useNavigate();

  async function logout() {
    await resetMe();
    navigate("/signin");
  }

  async function disconnect() {
    await api.post('disconnect-wallet');
    await reloadMe();
  }
</script>

<Section>
  <div class="outer">
    <div class="profile-button">
      <BaseButton
        --border-width=1px
        --border-color="rgba(0, 0, 0, 0.2)"
        --width=115px
        --height=32px
        --text-color=black
        --font-weight=500
        --font-size=12px
        link="/donator/me"
      >Profile</BaseButton>
    </div>
    <div class="content">
      <div class="image-and-name">
        {#await $me then me}
          <Userpic user={me.donator} class="userpic" --width=88px/>
          <MeNamePubkey align="center" />
        {/await}
      </div>
      <div class="controls">
        <div class="linked">
          {#await $me then me}
            <LinkedItems items={me.shortkey ? [{via_oauth: true}] : []} onUnlink={disconnect}>
              <div slot="header">
                Linked <b>Lightning</b> wallet:
              </div>
              <div class="linked-item" slot="item">
                <img alt='bolt' width=24px src="/static/bolt.svg"><span class="pubkey">{me.shortkey}</span>
              </div>
              <SocialSigninButton slot="add" height=48px width=min-content padding="0 20px" link="/login?return=/settings" idp="bolt">
                {#if me.shortkey}
                  Change Lightning wallet
                {:else}
                  Link Lightning wallet
                {/if}
              </SocialSigninButton>
            </LinkedItems>
          {/await}
          <LinkedItems let:item={channel} basePath="youtube" transferPath="channel" name="YouTube">
            <div class="linked-item" slot="item">
              <YoutubeChannel linkto="withdraw" channel={channel} logo --gap=16px />
            </div>
            <SocialSigninButton idp=youtube height=48px width=min-content padding="0 20px" slot=add returnTo="/settings">Link YouTube</SocialSigninButton>
          </LinkedItems>
          <LinkedItems let:item={account} basePath="twitter" transferPath="account" name="Twitter">
            <div class="linked-item" slot="item">
              <TwitterAccount account={account} --gap=16px />
            </div>
            <SocialSigninButton idp=twitter height=48px width=min-content padding="0 20px" slot=add returnTo="/settings">Link Twitter</SocialSigninButton>
          </LinkedItems>
        </div>
        {#await $me then me}
          {#if me.connected}
            <HoldButton
              on:click={logout}
              --border-width=1px
              --border-color=#E9E9E9
              --background-color=white
              --height=48px
              width=100%
              tooltipText="Hold to logout"
            >Logout</HoldButton>
          {/if}
        {/await}
      </div>
    </div>
  </div>
</Section>

<style>
.outer {
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.content {
  max-width: 560px;
  min-width: 300px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 0 40px;
  gap: 60px;
}
.profile-button {
  position: absolute;
  top: 24px;
  right: 24px;
}
.image-and-name {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}
.controls {
  display: flex;
  flex-direction: column;
  gap: 56px;
  width: 100%;
}
.linked {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 44px;
  width: 100%;
}
.linked::-webkit-scrollbar {
  display: none;  /* hide scroll for Safari and Chrome */
}
.linked-item {
  flex-grow: 100;
  display: flex;
  align-items: center;
  gap: 16px;
}
.pubkey {
  color: var(--link-color);
  font-weight: 700;
}
</style>
