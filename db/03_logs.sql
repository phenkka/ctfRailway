-- Таблица для логирования событий системы
create table if not exists logs (
    log_id bigserial primary key,
    event_type text not null
        check (event_type in (
            'api_request',
            'page_view', 
            'train_query',
            'train_filter',
            'date_select',
            'error',
            'train_detail_view'
        )),
    action text not null,
    details jsonb,
    ip_address inet,
    user_agent text,
    status_code int,
    execution_time_ms int,
    created_at timestamp default now()
);

-- Индексы для быстрого поиска
create index if not exists idx_logs_event_type on logs(event_type);
create index if not exists idx_logs_created_at on logs(created_at);
create index if not exists idx_logs_action on logs(action);
create index if not exists idx_logs_status_code on logs(status_code);

