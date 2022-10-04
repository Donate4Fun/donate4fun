<section>
  <div>
    <slot />
  </siv>
</section>

<style>
section {
  background: #FFFFFF;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 20px;
  min-width: 240px;
  height: 288px;
  background-image: linear-gradient(to right, #F9F03E80 0%, #9DEDA280 100%);
  padding: var(--border-width, 0);
}
section:hover {
}
div {
  background: #FFFFFF;
  border-radius: calc(20px - var(--border-width, 0px));
  padding: calc(32px - var(--border-width, 0px)) calc(20px - var(--border-width, 0px));
} 
</style>
