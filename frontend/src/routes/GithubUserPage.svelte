<script>
  import GithubUser from "$lib/GithubUser.svelte";

  export let user_id;
</script>

<SocialAccountPage account_id={user_id} provider="github">
  <GithubUser slot="target" let:account={user} externalLink={true} imagePlacement=after --image-size=44px user={user} />
</SocialAccountPage>
