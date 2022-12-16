with orig as (
  select sum(amount) as total_donated, twitter_account_id as id
  from donation
  where paid_at is not null and cancelled_at is null and twitter_account_id is not null
  group by twitter_account_id
)
select orig.total_donated, a.total_donated, id
from twitter_author a
join orig using (id)
where orig.total_donated != a.total_donated;
