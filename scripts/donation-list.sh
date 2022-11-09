#!/bin/sh -e

./scripts/psql.sh -c '
  select paid_at, amount, ytc.title, dr.name
  from donation d
  join youtube_channel ytc on d.youtube_channel_id = ytc.id
  left join donator dr on dr.id = d.donator_id
  where paid_at is not null order by paid_at desc;
'
