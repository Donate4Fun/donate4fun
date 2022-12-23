<script>
  export let src;
  export let social;
</script>

<div class="userpic">
  <img {src} alt="avatar">
  <div class="social">
    <img alt={social} src="/static/{social}.svg">
  </div>
</div>

<style>
.userpic {
  position: relative;
  width: 46px;
  height: 46px;
}
.userpic > img {
  border-radius: 100px;
  width: 44px;
  height: 44px;
}
.social {
  width: 20px;
  height: 20px;
  border-radius: 100px;
  background-color: white;
  position: absolute;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  box-shadow: 2px 2px 12px rgba(162, 168, 179, 0.5);
  padding: 5px;
}
</style>
