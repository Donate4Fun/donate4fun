<div><span><slot /></span></div>

<style>
div {
  background: linear-gradient(180deg, 
    rgba(0,0,0,0) calc(50% - 1px), 
    rgba(0,0,0,0.1) calc(50%), 
    rgba(0,0,0,0) calc(50% + 1px)
  );
  width: 100%;
  text-align: center;
}
span {
  background: white;
  padding: 0 6px;
  font-weight: 500;
  font-size: 16px;
}
</style>
