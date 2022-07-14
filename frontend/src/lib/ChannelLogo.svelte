<script>
  export let url;
  export let size = "72px";
</script>

<img class="channel-logo" src={url} style="--size: {size}" alt="logo">

<style>
img {
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
}
</style>
