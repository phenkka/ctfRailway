create table if not exists trains (
    train_id serial primary key,
    type_train text not null
        check (type_train in ('suburban', 'express', 'mail', 'long-distance')),
    train_brand text not null
);

create table if not exists routes (
    route_id bigserial primary key,
    train_id int not null references trains(train_id) on update cascade,
    route_from text not null,
    route_to text not null,
    arrival_time time,
    departure_time time,
    platform int
        check (platform in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)),
    created_at timestamp default now()
);
create unique index if not exists uq_platform_departure_time on routes(platform, departure_time);

