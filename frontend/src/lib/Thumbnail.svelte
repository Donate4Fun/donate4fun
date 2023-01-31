<script>
  export let url;
  export let size = '2em';
</script>

<img src={url} style:width={size} alt="thumbnail">

<style>
img {
  border-radius: 50%;
}
</style>
