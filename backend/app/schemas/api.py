from pydantic import BaseModel
from typing import List, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    status: int = 200
    errors: Optional[Dict[str, List[str]]] = None
    