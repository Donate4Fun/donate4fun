#!/bin/sh -e

./scripts/psql.sh -c 'copy (
  select date(paid_at) as dt, sum(amount) as amount
  from withdrawal w
  where paid_at is not null
  group by dt
  order by dt
  ) to stdout;' | termgraph "$@"
