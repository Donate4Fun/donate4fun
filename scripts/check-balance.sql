with orig as (
  select
    sum(amount) as total_donated,
    coalesce(twitter_account_id, youtube_channel_id, github_user_id) as id,
    sum(case when claimed_at is null and lightning_address is null then amount else 0 end) as balance,
    sum(case when lightning_address is not null then amount else 0 end) as lightning_amount,
    sum(case when lightning_address is null and claimed_at is not null then amount else 0 end) as claimed
  from donation
  where paid_at is not null
    and cancelled_at is null
    and (twitter_account_id is not null or youtube_channel_id is not null)
  group by coalesce(twitter_account_id, youtube_channel_id)
)
, transfers as (
  select coalesce(twitter_author_id, youtube_channel_id, github_user_id) as id, sum(amount) as amount_transferred
  from transfer
  group by coalesce(twitter_author_id, youtube_channel_id, github_user_id)
)
, targets as (
  select total_donated, balance, id, 'twitter' as type, handle as name
  from twitter_author
  union
  select total_donated, balance, id, 'youtube' as type, title as name
  from youtube_channel
)
, links as (
  select youtube_channel_id as id
  from youtube_channel_link
  union
  select twitter_author_id as id
  from twitter_author_link
  union
  select github_user_id as id
  from github_user_link
)
select
  orig.total_donated as don_total,
  targets.total_donated as acc_total,
  orig.balance as don_balance,
  targets.balance as acc_balance,
  orig.lightning_amount as by_light,
  orig.claimed as don_claimed,
  transfers.amount_transferred as claimed,
  id,
  type,
  name,
  links.id is not null as linked
from orig
left join targets using (id)
left join transfers using (id)
left join links using (id)
where
  orig.balance != targets.balance
  or orig.total_donated != targets.total_donated;
