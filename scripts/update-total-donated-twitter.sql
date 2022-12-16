with orig as (
  select sum(amount) as total_donated, twitter_account_id as id
  from donation
  where paid_at is not null and cancelled_at is null and twitter_account_id is not null
  group by twitter_account_id
)
update twitter_author
set total_donated = orig.total_donated
from orig
where twitter_author.id = orig.id and twitter_author.total_donated != orig.total_donated;
