import requests
from typing import List
from config import NOTIFY_KEY, NOTIFY_URL


def notify_result(work_id: str, result: List, context: str, calc_type: str, is_save_to_dict: bool = False) -> bool:
    requests.post(NOTIFY_URL, json={
        'work_id': work_id,
        'result': result,
        'context': context,
        'is_save_to_dict': is_save_to_dict,
        'calc_type': calc_type,  # origin,parsed
        'key': NOTIFY_KEY
    })
    return True
