<script>
  import { errorToText } from "$lib/api.js";

  export let error = "Page not found";
</script>

<h3>Page not found</h3>
<div>{ error ? errorToText(error.response) : error }</div>
