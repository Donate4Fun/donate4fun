<script>
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import SocialAccountPage from "$lib/SocialAccountPage.svelte";

  export let account_id;
</script>

<SocialAccountPage {account_id} provider="twitter">
  <TwitterAccount slot="target" externalLink={true} showHandle={false} imagePlacement=after --image-size=44px let:account={account} account={account} />
</SocialAccountPage>
