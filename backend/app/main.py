from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Expense, IdempotencyRecord
from .schemas import ExpenseCreate, ExpenseResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BEST_EFFORT_HASH_DEDUPE_WINDOW = timedelta(minutes=2)


def _request_hash(payload: ExpenseCreate) -> str:
    canonical = {
        "amount": str(payload.amount.quantize(Decimal("0.01"))),
        "category": payload.category,
        "description": payload.description,
        "date": payload.date.isoformat(),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@app.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    req_hash = _request_hash(payload)

    if idempotency_key:
        existing = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.key == idempotency_key))
        if existing:
            response.status_code = status.HTTP_200_OK
            return existing.expense

    # Fallback for retry scenarios where no key is present.
    cutoff = datetime.now(UTC) - BEST_EFFORT_HASH_DEDUPE_WINDOW
    recent_same = db.scalar(
        select(IdempotencyRecord)
        .where(IdempotencyRecord.request_hash == req_hash, IdempotencyRecord.created_at >= cutoff)
        .order_by(desc(IdempotencyRecord.created_at))
    )
    if recent_same:
        response.status_code = status.HTTP_200_OK
        return recent_same.expense

    expense = Expense(
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        date=payload.date,
    )
    db.add(expense)
    db.flush()

    record_key = idempotency_key or f"hash:{req_hash}:{int(datetime.now(UTC).timestamp())}"
    idempotency_record = IdempotencyRecord(
        key=record_key,
        request_hash=req_hash,
        expense_id=expense.id,
    )
    db.add(idempotency_record)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        if idempotency_key:
            existing = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.key == idempotency_key))
            if existing:
                response.status_code = status.HTTP_200_OK
                return existing.expense
        raise HTTPException(status_code=500, detail="Could not create expense") from exc

    db.refresh(expense)
    return expense


@app.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Expense)
    if category:
        query = query.where(Expense.category == category)
    if sort == "date_desc":
        query = query.order_by(desc(Expense.date), desc(Expense.created_at))
    else:
        query = query.order_by(desc(Expense.created_at))

    return list(db.scalars(query).all())
