#!/bin/sh -e

./scripts/psql.sh -c '
  select paid_at, amount, ytc.title, twa.name, substring(don.lnauth_pubkey, 1, 7) as pubkey
  from withdrawal w
  left join youtube_channel ytc on w.youtube_channel_id = ytc.id
  left join twitter_author twa on w.twitter_author_id = twa.id
  left join donator don on w.donator_id = don.id
  where paid_at is not null
  order by paid_at;'
