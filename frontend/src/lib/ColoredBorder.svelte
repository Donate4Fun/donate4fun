<div class="outer">
  <div class="inner">
    <slot />
  </div>
</div>

<style>
.outer {
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  padding: 2px;
  border-radius: 1000px;
  width: 100%;
  height: 100%;
}
.inner {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background-color: var(--background-color, white);
}
</style>
