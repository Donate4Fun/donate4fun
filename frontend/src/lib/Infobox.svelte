<div class="outer">
  <img src="/exclamation.svg" alt="exclamation">
  <div>
    <slot />
  </div>
</div>

<style>
.outer {
  display: flex;
  align-content: center;
  background: rgba(0, 78, 231, 0.07);
  border-radius: 8px;
  padding: 1em;
}
.outer > img {
  margin-right: 1em;
}
</style>
