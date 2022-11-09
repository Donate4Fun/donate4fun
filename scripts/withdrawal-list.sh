#!/bin/sh -e

./scripts/psql.sh -c '
  select paid_at, amount, ytc.title
  from withdrawal w
  join youtube_channel ytc on w.youtube_channel_id = ytc.id
  where paid_at is not null
  order by paid_at;'
