<script>
  import { link, useNavigate } from "svelte-navigator";

  import Userpic from "$lib/Userpic.svelte";
  import Section from "$lib/Section.svelte";
  import Donator from "$lib/Donator.svelte";
  import Button from "$lib/Button.svelte";
  import BaseButton from "$lib/BaseButton.svelte";
  import MeNamePubkey from "$lib/MeNamePubkey.svelte";
  import MeBalance from "$lib/MeBalance.svelte";
  import Title from "$lib/Title.svelte";
  import DonatorHistory from "$lib/DonatorHistory.svelte";
  import { syncMe as me } from "$lib/session.js";
  import { apiStore } from "$lib/api.js";
  import title from "$lib/title.js";

  export let donator_id;

  $: donator = apiStore(`donator/${donator_id}`, `donator:${donator_id}`);
  $: itsMe = donator_id === $me?.donator?.id;
</script>

{#if $donator}
  <Title title="{$donator.name} profile" />
  <Section>
    <div class="main">
      {#if itsMe}
        <div class="settings-button">
          <BaseButton
            --border-width=1px
            --border-color="rgba(0, 0, 0, 0.2)"
            --width=115px
            --height=32px
            --text-color=black
            --font-weight=500
            --font-size=12px
            link="/settings"
          >Settings</BaseButton>
        </div>
      {/if}
      <div class="top-block">
        <div class="image-and-name">
          <Userpic user={$donator} class="userpic" --width=88px/>
          {#if itsMe}
            <MeNamePubkey align="center" />
          {:else}
            <p>{$donator.name}</p>
          {/if}
        </div>
        {#if itsMe}
          <div class="balance-actions">
            {#if $me.connected}
              <MeBalance />
            {:else}
              <Button link="/signin">Sign in</Button>
            {/if}
          </div>
        {:else}
          <Button link="/fulfill/{donator_id}">Donate</Button>
        {/if}
      </div>
      {#if itsMe}
        <DonatorHistory {donator_id} />
      {/if}
    </div>
  </Section>
{/if}

<style>
.main {
  display: flex;
  flex-direction: column;
  gap: 64px;
  padding: 40px 34px;
  position: relative;
}
@media (max-width: 639px) {
  .main {
    width: 100vw;
  }
}
@media (min-width: 640px) {
  .main {
    width: 640px;
    align-items: center;
  }
}
.settings-button {
  position: absolute;
  right: 24px;
  top: 24px;
}
.top-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}
.image-and-name {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}
.balance-actions {
  width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
</style>
