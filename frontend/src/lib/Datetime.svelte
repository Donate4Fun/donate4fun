<script>
  import dateFormat, { masks } from "dateformat";

  export let dt;

  $: dtString = (() => {
    if (dt !== null) {
      const elapsed = (Date.now() - (new Date(dt)).getTime()) / 86_400_000;
      return dateFormat(dt, elapsed < 7 ? "DDDD HH:MM" : "mediumDate")
    } else {
      return "";
    }
  })();
</script>

{dtString}
