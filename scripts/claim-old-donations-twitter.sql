update donation set claimed_at = now()
where id in (
  select
    sq.id
  from (
      select id, paid_at, twitter_account_id, amount, sum(amount) over (partition by twitter_account_id order by paid_at desc) as wnd_amount
      from donation
      where twitter_account_id is not null and paid_at is not null and cancelled_at is null
  ) sq
  join twitter_author twa on twa.id = sq.twitter_account_id
  where twa.balance < wnd_amount
  order by twa.id, paid_at
);
