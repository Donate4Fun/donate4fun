<div class="root">
  <div class="arrow">
    <div class="rect left"></div>
    <div class="rect right"></div>
  </div>
  <div class="arrow delay1">
    <div class="rect left"></div>
    <div class="rect right"></div>
  </div>
</div>

<style>
.root {
  display: flex;
  align-content: center;
  --time: 1s;
  --skew: 30deg;
  --height: 12px;
  --inner-height: 7px;
  --arrow-width: 12px;
  --arrow-height: 5px;
  width: var(--arrow-width);
  height: calc(var(--height));
  transform: translateY(calc(var(--inner-height) / 2 + 1px));
}
@keyframes slide-y {
    0% { opacity:0; transform: translateY(calc(var(--height) / -2)); }
   20% { opacity:1; transform: translateY(calc(var(--inner-height) / -2)); }
   80% { opacity:1; transform: translateY(calc(var(--inner-height) / 2)); }
  100% { opacity:0; transform: translateY(calc(var(--height) / 2)); }
}
.arrow {
  display: flex;
  position: absolute;
  animation: slide-y var(--time) linear infinite;
}
.rect {
  width: calc(var(--arrow-width) / 2);
  height: var(--arrow-height);
  background-color: var(--color, black);
  border-radius: 1px;
}
.rect.left {
  transform: skewY(var(--skew));
}
.rect.right {
  transform: skewY(calc(var(--skew) * -1));
}
.delay1 {
  animation-delay: calc(var(--time) / -2);
}
</style>
