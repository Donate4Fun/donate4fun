#!/bin/sh -e

./scripts/psql.sh -c 'copy (select date(paid_at) as dt, amount from withdrawal w join youtube_channel ytc on w.youtube_channel_id = ytc.id where paid_at is not null order by dt) to stdout;' | termgraph "$@"
