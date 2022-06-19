<script>
  export let dt;

  $: dtString = (() => {
    if (dt !== null) {
      return (new Date(dt)).toLocaleString("ru-RU");
    } else {
      return "";
    }
  })();
</script>

{dtString}
