# FastAPI

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter(prefix="/patients", tags=["patients"])
Db = Annotated[Session, Depends(get_db)]       # dependency injection

@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Db) -> PatientOut:      # path param, parsed + validated
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientOut.model_validate(patient)

@router.get("")
def search(db: Db, state: str, page: Annotated[int, Query(ge=1)] = 1): ...   # query params

@router.post("", status_code=status.HTTP_201_CREATED)
def create(body: PatientCreate, db: Db): ...                  # JSON body (Pydantic model)
```

- Request validation failures → **422** automatically. Uncaught exceptions → **500**.
- `Depends(fn)`: called per request; `yield` in a dependency = setup/teardown (DB session).
- Custom errors: `@app.exception_handler(DomainError)` → return a `JSONResponse`.
- `response.status_code = 200` via a `response: Response` parameter to change it dynamically.
- `def` endpoints run in a thread pool; `async def` ones on the event loop (never block in them).

**Tests:**
```python
client = TestClient(app)
app.dependency_overrides[get_db] = lambda: test_session
r = client.post("/patients", json={...}); assert r.status_code == 201, r.json()
```
