<script>
  import { link, useNavigate } from "svelte-navigator";
  import { syncMe as me } from "$lib/session.js";
  const navigate = useNavigate();
  $: {
    if ($me !== null)
      navigate(`/donator/${$me.donator.id}`, {replace: true});
  }
</script>
