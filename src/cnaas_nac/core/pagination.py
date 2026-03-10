from fastapi import Query


# FastAPI Dependency
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=0, le=1000, description="Items per page"),
    ):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
