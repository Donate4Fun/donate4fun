<div class=outer>
  <div class=inner>
    <div class=absolute>
      <slot />
    </div>
  </div>
</div>

<style>
.outer {
  position: relative;
  height: 100%;
  width: 100%;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  ---border-color: var(--border-color, rgba(26, 41, 82, 0.05));
  ---border-width: var(--border-width, 0px);
  ---border-radius: var(--border-radius, 20px);
  background: var(---border-color);
  padding: var(---border-width);
  border-radius: var(---border-radius);
  transition: all 0.2s ease;
}
.outer:hover {
  --border-width: 6px;
  --border-color: linear-gradient(#F9F03E80, #9DEDA280);
}
.inner {
  background: #FFFFFF;
  width: 100%;
  height: 100%;
  border-radius: calc(var(---border-radius) - var(---border-width));
}
.absolute {
  position: absolute;
  top: 0;
  left: 0;
  background: transparent;
  width: 100%;
  height: 100%;
}
</style>
