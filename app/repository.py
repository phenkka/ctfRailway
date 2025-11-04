from typing import List

from db.pool import get_conn
from models import TrainWithRoute


async def get_all_trains_with_routes() -> List[TrainWithRoute]:
    async for conn in get_conn():
        rows = await conn.fetch("""
            SELECT 
                t.train_id,
                t.type_train,
                t.train_brand,
                r.route_id,
                r.route_from,
                r.route_to,
                r.arrival_time::text as arrival_time,
                r.departure_time::text as departure_time,
                r.platform
            FROM trains t
            INNER JOIN routes r ON t.train_id = r.train_id
            ORDER BY r.departure_time ASC
        """)
        
        return [
            TrainWithRoute(
                train_id=row['train_id'],
                type_train=row['type_train'],
                train_brand=row['train_brand'],
                route_id=row['route_id'],
                route_from=row['route_from'],
                route_to=row['route_to'],
                arrival_time=row['arrival_time'],
                departure_time=row['departure_time'],
                platform=row['platform']
            )
            for row in rows
        ]
    return []