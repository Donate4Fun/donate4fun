<div class="parent">
  <div class="full">
    <div class="stroke-text">
      <svg class="back" height=40 width=200>
        <text class="stroke" x="5px" y="33px">
          Donate4Fun
        </text>
      </svg>
      <div class="text">Donate4Fun</div>
    </div>
  </div>
</div>

<style>
.full {
  font-weight: 900;
  font-size: 29px;
  display: flex;
  gap: 6px;
  align-items: center;
}
.full .text {
  background: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%), linear-gradient(299.9deg, #FF7A00 18.72%, #FFA800 82.21%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
  padding: 0 5px;
}
.stroke-text {
  position: relative;
  height: 36px;
  width: 200px;
}
.back {
  position: absolute;
  z-index: -1;
  bottom: 0;
}
div.text {
  position: absolute;
  bottom: 0;
}
.stroke {
  stroke: #2E6CFF;
  stroke-width: 8px;
  fill: none;
}
</style>
