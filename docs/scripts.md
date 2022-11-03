## Convert mkv to looped webp

```
ffmpeg -i sample2.mkv -loop 0 -an -vsync 0 -vf "scale=300:200" ~/src/donate4.fun/frontend/public/static/bolt-example.webp
```
