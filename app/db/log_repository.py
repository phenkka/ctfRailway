from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json

from db.pool import get_conn
from api.models import Log, LogCreate


async def create_log(log_data: LogCreate) -> Optional[int]:
    try:
        async for conn in get_conn():
            query = """
                INSERT INTO logs (event_type, action, details, ip_address, user_agent, status_code, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING log_id
            """
            details_json = json.dumps(log_data.details) if log_data.details else None
            
            result = await conn.fetchrow(
                query,
                log_data.event_type,
                log_data.action,
                details_json,
                log_data.ip_address,
                log_data.user_agent,
                log_data.status_code,
                log_data.execution_time_ms
            )
            return result['log_id'] if result else None
    except Exception as e:
        # В случае ошибки логирования не прерываем выполнение программы
        print(f"Ошибка при создании лога: {e}")
        return None


async def get_logs(
    event_type: Optional[str] = None,
    action: Optional[str] = None,
    status_code: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Log]:
    async for conn in get_conn():
        conditions = []
        params = []
        param_index = 1
        
        if event_type:
            conditions.append(f"event_type = ${param_index}")
            params.append(event_type)
            param_index += 1
            
        if action:
            conditions.append(f"action LIKE ${param_index}")
            params.append(f"%{action}%")
            param_index += 1
            
        if status_code:
            conditions.append(f"status_code = ${param_index}")
            params.append(status_code)
            param_index += 1
            
        if start_date:
            conditions.append(f"DATE(created_at) >= ${param_index}")
            params.append(start_date)
            param_index += 1
            
        if end_date:
            conditions.append(f"DATE(created_at) <= ${param_index}")
            params.append(end_date)
            param_index += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                log_id,
                event_type,
                action,
                details,
                ip_address::text as ip_address,
                user_agent,
                status_code,
                execution_time_ms,
                created_at
            FROM logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_index} OFFSET ${param_index + 1}
        """
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        
        logs = []
        for row in rows:
            details = None
            if row['details']:
                try:
                    if isinstance(row['details'], str):
                        details = json.loads(row['details'])
                    else:
                        details = row['details']
                except:
                    details = row['details']
            
            log = Log(
                log_id=row['log_id'],
                event_type=row['event_type'],
                action=row['action'],
                details=details,
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                status_code=row['status_code'],
                execution_time_ms=row['execution_time_ms'],
                created_at=row['created_at']
            )
            logs.append(log)
        
        return logs
    return []


async def get_logs_count(
    event_type: Optional[str] = None,
    action: Optional[str] = None,
    status_code: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    async for conn in get_conn():
        conditions = []
        params = []
        param_index = 1
        
        if event_type:
            conditions.append(f"event_type = ${param_index}")
            params.append(event_type)
            param_index += 1
            
        if action:
            conditions.append(f"action LIKE ${param_index}")
            params.append(f"%{action}%")
            param_index += 1
            
        if status_code:
            conditions.append(f"status_code = ${param_index}")
            params.append(status_code)
            param_index += 1
            
        if start_date:
            conditions.append(f"DATE(created_at) >= ${param_index}")
            params.append(start_date)
            param_index += 1
            
        if end_date:
            conditions.append(f"DATE(created_at) <= ${param_index}")
            params.append(end_date)
            param_index += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT COUNT(*) as count
            FROM logs
            WHERE {where_clause}
        """
        
        result = await conn.fetchrow(query, *params)
        return result['count'] if result else 0
    return 0

