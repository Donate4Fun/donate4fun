<script>
  import { link } from "svelte-navigator";

  import WhiteButton from "$lib/WhiteButton.svelte";
  import TwitterShare from "$lib/TwitterShare.svelte";
  import EmbeddedTweet from "$lib/EmbeddedTweet.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import ColoredBorder from "$lib/ColoredBorder.svelte";

  export let donation;
</script>

<div class="container">
  <div class="main">
    {#if donation.donator_twitter_account}
      <a use:link href="/twitter/{donation.donator_twitter_account.id}" class="twitter-account">
        <div class="image-name">
          <img alt="avatar" class="avatar" src={donation.donator_twitter_account.profile_image_url}>
          <div class="name">{donation.donator_twitter_account.name}</div>
        </div>
        <div class="handle">@{donation.donator_twitter_account.handle}</div>
      </a>
    {:else}
      <div class="image-name">
        <img alt="avatar" class="avatar" src={donation.donator.avatar_url}>
        <div class="name">{donation.donator.name}</div>
      </div>
    {/if}
    <div class="amount blue">sent <b>{donation.amount} sats</b> to</div>
    <a use:link href="/twitter/{donation.twitter_account.id}" class="twitter-account">
      <div class="image-name">
        <img alt="avatar" class="avatar" src={donation.twitter_account.profile_image_url}>
        <div class="name">{donation.twitter_account.name}</div>
      </div>
      <div class="handle">
        <span>@{donation.twitter_account.handle}</span>
        {#if donation.lightning_address}
          <span class="lightning-address">via ⚡{donation.lightning_address}</span>
        {/if}
      </div>
    </a>
  </div>
  {#if donation.cancelled_at === null && donation.claimed_at === null}
    <div class="claim">
      <SocialSigninButton colored height=48px width=300px type="twitter">Claim with Twitter</SocialSigninButton>
    </div>
  {/if}
  {#if donation.twitter_tweet !== null}
    <EmbeddedTweet id={donation.twitter_tweet.tweet_id} />
  {/if}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;

  font-weight: 900;
  font-size: 24px;
}
.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #2E6CFF;
}
.twitter-account {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: "Montserrat", "Twemoji", "TwitterChirp";
  color: inherit;
}
.image-name {
  display: flex;
  gap: 12px;
}
img.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  --filter: drop-shadow(4px 4px 20px rgba(34, 60, 103, 0.15)) drop-shadow(10px 15px 25px rgba(209, 217, 230, 0.4));
  border: 2px solid #FFFFFF;
  box-shadow: 4px 4px 20px rgba(34, 60, 103, 0.15), 10px 15px 25px rgba(209, 217, 230, 0.4);
}
.name {
  color: inherit;
  font-weight: 900;
  font-size: 24px;
  line-height: 29px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.handle {
  display: flex;
  gap: 8px;

  font-weight: 500;
  font-size: 12px;
  line-height: 15px;
  padding-left: 44px;
}
.lightning-address {
  color: var(--color);
}
.amount {
  padding-left: 44px;
  font-weight: 400;
  font-size: 24px;
  line-height: 29px;
  color: inherit;
}
.amount b {
  color: #19B400;
  font-weight: 800;
}
.claim {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}
@media (max-width: 640px) {
  .name,.amount {
    font-size: 20px;
    line-height: 24px;
  }
}
</style>
