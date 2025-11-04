-- Базовые поезда (если их ещё нет)
INSERT INTO trains(type_train, train_brand)
SELECT v.type_train, v.train_brand
FROM (
    VALUES
        ('suburban', 'РАЗ'),
        ('express',  'Ласточка'),
        ('express',  'Финист'),
        ('mail',     'Почта-РЖД'),
        ('long-distance', 'РЖД-ЛД')
) AS v(type_train, train_brand)
WHERE NOT EXISTS (
    SELECT 1 FROM trains t WHERE t.train_brand = v.train_brand
);

-- Расписание для вокзала Екатеринбург
-- Правила:
-- - если поезд только приезжает в Екатеринбург: arrival_time заполнен, departure_time = NULL
-- - если поезд только отправляется из Екатеринбурга: arrival_time = NULL, departure_time заполнен
-- - если Екатеринбург — промежуточная станция: заполнены оба времени

BEGIN;

INSERT INTO routes (train_id, route_from, route_to, arrival_time, departure_time)
VALUES
-- Ночные и ранние утренние прибытия (только arrival)
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Казань', 'Екатеринбург', '02:03', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Пермь', 'Екатеринбург', '02:25', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Сургут', 'Екатеринбург', '02:47', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Нижний Тагил', 'Екатеринбург', '03:05', NULL),

-- Ранние отправления (только departure)
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Тюмень', NULL, '03:10'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Челябинск', NULL, '03:22'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Берёзовский', NULL, '03:35'),

-- Сквозные (Екатеринбург — промежуточный)
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Уфа', 'Пермь', '03:40', '03:48'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Курган', 'Нижний Тагил', '04:05', '04:12'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Тюмень', 'Челябинск', '04:20', '04:28'),

-- Прибытия волной
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Омск', 'Екатеринбург', '04:45', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Каменск-Уральский', 'Екатеринбург', '04:57', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Тобольск', 'Екатеринбург', '05:10', NULL),

-- Отправления волной
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Невьянск', NULL, '05:18'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Пермь', NULL, '05:25'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Курган', NULL, '05:37'),

-- Одновременные прибытие и отправление разных поездов (платформы потом назначит скрипт)
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Новосибирск', 'Екатеринбург', '06:00', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Челябинск', NULL, '06:00'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Новоуральск', NULL, '06:00'),

-- Сквозные ещё
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Ижевск', 'Челябинск', '06:12', '06:20'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Санкт-Петербург', 'Омск', '06:30', '06:40'),

-- Ещё прибытия
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Казань', 'Екатеринбург', '06:55', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Нижний Тагил', 'Екатеринбург', '07:07', NULL),

-- Ещё отправления
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Пермь', NULL, '07:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Тюмень', NULL, '07:22'),

-- Сквозной трафик
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Самара', 'Челябинск', '07:40', '07:48'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Казань', 'Курган', '07:55', '08:03'),

-- Утренняя волна прибытия/отправления
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Каменск-Уральский', 'Екатеринбург', '08:10', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Челябинск', 'Екатеринбург', '08:15', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Сургут', NULL, '08:15'),

-- Синхронные события
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Тюмень', 'Екатеринбург', '08:30', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Берёзовский', NULL, '08:30'),

-- Сквозные
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Москва', 'Новосибирск', '08:45', '08:55'),

-- Ближе к 9
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Новоуральск', 'Екатеринбург', '09:05', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Казань', NULL, '09:10'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Челябинск', NULL, '09:18'),

-- Пиковые сквозные
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Сочи', 'Тюмень', '09:30', '09:40'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Омск', 'Пермь', '09:50', '09:58'),

-- К 10 утра
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Томск', 'Екатеринбург', '10:05', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Невьянск', 'Екатеринбург', '10:12', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Тюмень', NULL, '10:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Пермь', NULL, '10:22');

COMMIT;

-- Продолжение расписания: с 10:30 до 23:00, с ограничением 12:00–15:00 только почтовые поезда
BEGIN;

INSERT INTO routes (train_id, route_from, route_to, arrival_time, departure_time)
VALUES
-- 10:30–11:59 — обычный режим
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Серов', 'Екатеринбург', '10:30', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Нижний Тагил', NULL, '10:32'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Москва', 'Тюмень', '10:45', '10:55'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Пермь', NULL, '11:05'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Берёзовский', 'Екатеринбург', '11:12', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Курган', NULL, '11:20'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Омск', 'Самара', '11:30', '11:38'),

-- 12:00–14:59 — только почтовые (Почта-РЖД)
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Казань', 'Екатеринбург', '12:03', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Екатеринбург', 'Челябинск', NULL, '12:20'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Пермь', 'Екатеринбург', '12:55', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Екатеринбург', 'Тюмень', NULL, '13:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Тюмень', 'Екатеринбург', '13:40', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Екатеринбург', 'Пермь', NULL, '14:05'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Челябинск', 'Екатеринбург', '14:40', NULL),

-- 15:00–17:59 — обычный режим
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Пермь', NULL, '15:05'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Каменск-Уральский', 'Екатеринбург', '15:12', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Тюмень', 'Челябинск', '15:20', '15:28'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Санкт-Петербург', 'Омск', '15:35', '15:45'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Казань', NULL, '16:00'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Невьянск', NULL, '16:10'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Новосибирск', 'Москва', '16:25', '16:35'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Сургут', 'Екатеринбург', '16:50', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Новоуральск', NULL, '17:00'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Пермь', 'Екатеринбург', '17:12', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Самара', 'Челябинск', '17:30', '17:38'),

-- 18:00–20:59 — вечерние волны
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Тюмень', NULL, '18:05'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Невьянск', 'Екатеринбург', '18:12', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Курган', NULL, '18:20'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Москва', 'Новосибирск', '18:40', '18:50'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Омск', 'Екатеринбург', '19:05', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Берёзовский', NULL, '19:10'),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Челябинск', 'Екатеринбург', '19:18', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Пермь', NULL, '19:25'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Омск', 'Самара', '19:40', '19:48'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Новоуральск', 'Екатеринбург', '20:05', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Тюмень', NULL, '20:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Курган', 'Екатеринбург', '20:28', NULL),

-- 21:00–23:00 — поздние рейсы
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Новосибирск', 'Москва', '21:10', '21:20'),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Невьянск', NULL, '21:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Екатеринбург', 'Казань', NULL, '21:25'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Пермь', 'Екатеринбург', '21:40', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Челябинск', NULL, '21:50'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Самара', 'Челябинск', '22:05', '22:15'),
((SELECT train_id FROM trains WHERE train_brand = 'Ласточка'), 'Пермь', 'Екатеринбург', '22:20', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'РАЗ'), 'Екатеринбург', 'Берёзовский', NULL, '22:25'),
((SELECT train_id FROM trains WHERE train_brand = 'Почта-РЖД'), 'Челябинск', 'Екатеринбург', '22:40', NULL),
((SELECT train_id FROM trains WHERE train_brand = 'Финист'), 'Екатеринбург', 'Тюмень', NULL, '22:50'),
((SELECT train_id FROM trains WHERE train_brand = 'РЖД-ЛД'), 'Тюмень', 'Москва', '22:55', '23:00');

COMMIT;
