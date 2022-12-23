<button on:click>
  <img src="/static/youtube.svg">
  <span>Sign in with YouTube</span>
</button>

<style>
button {
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 40px;
  width: min-content;
  cursor: pointer;
  white-space: nowrap;
  border-radius: 4px;
  border-width: 1px;
  border-color: rgb(210, 227, 252);
  border-style: solid;
  background-color: white;
  transition-property: background-color 0.218s;
}
button:hover {
  background-color: rgba(66, 133, 244, 0.04);
}
button span {
  font-family: "Google Sans";
  font-weight: 500;
  font-size: 14px;
  color: rgb(60, 64, 67);
}
button img {
  height: 18px;
}
@font-face {
  font-family: "Google Sans";
  src: url("https://fonts.gstatic.com/s/googlesans/v45/4UasrENHsxJlGDuGo1OIlJfC6l_24rlCK1Yo_Iqcsih3SAyH6cAwhX9RPjIUvQ.woff2") format("woff2");
}
</style>
