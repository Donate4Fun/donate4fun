<script>
  export let value;
</script>

<label class="switch">
  <input type="checkbox" bind:checked={value} on:change>
  <span class="slider"></span>
</label>

<style>
.switch {
  position: relative;
  display: inline-block;
  width: 38px;
  height: 18px;
}

/* Hide default HTML checkbox */
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

/* The slider */
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  transition: .4s;
  border-radius: 100px;
  background: rgba(0, 0, 0, 0.0241);
  border: 1px solid rgba(0, 0, 0, 0.4458);
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 4px;
  top: calc(50% - 12px/2);
  transition: .4s;
  border-radius: 100px;
  background: rgba(0, 0, 0, 0.6063);
}

input:checked + .slider {
  background: linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%);
}

input:focus + .slider {
  box-shadow: 0 0 1px #2196F3;
}

input:checked + .slider:before {
  transform: translateX(18px);
  background: #FFFFFF;
  box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
}
</style>
