update donation set claimed_at = now()
where id in (
  select
    sq.id
  from (
      select id, paid_at, youtube_channel_id, amount, sum(amount) over (partition by youtube_channel_id order by paid_at desc) as wnd_amount
      from donation
      where youtube_channel_id is not null and paid_at is not null and cancelled_at is null
  ) sq
  join youtube_channel ytc on ytc.id = sq.youtube_channel_id
  where ytc.balance < wnd_amount
  order by ytc.id, paid_at
);
