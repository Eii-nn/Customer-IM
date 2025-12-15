from datetime import datetime, date
from decimal import Decimal

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session


app = Flask(__name__)
CORS(app)

engine = create_engine("sqlite:///salay_glass.db", echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False)
    contact = Column(String(255), nullable=True)
    description = Column(String(1024), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), nullable=False)
    balance = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    transaction_date = Column(Date, default=date.today, nullable=False)

    items = relationship("LineItem", back_populates="transaction", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    item_description = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    transaction = relationship("Transaction", back_populates="items")


def init_db():
    Base.metadata.create_all(bind=engine)


@app.teardown_appcontext
def remove_session(exception=None):
    SessionLocal.remove()


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/transactions")
def create_transaction():
    data = request.json or {}
    session = SessionLocal()

    try:
        customer_name = (data.get("customer_name") or "").strip()
        description = (data.get("description") or "").strip()
        contact = (data.get("contact") or "").strip()
        items_data = data.get("items") or []
        amount_paid = Decimal(str(data.get("amount_paid") or "0"))

        if not customer_name:
            return jsonify({"error": "Customer name is required."}), 400
        if not description:
            return jsonify({"error": "Overall job description is required."}), 400
        if not items_data:
            return jsonify({"error": "At least one line item is required."}), 400

        items: list[LineItem] = []
        total_amount = Decimal("0.00")

        for item in items_data:
            item_desc = (item.get("item_description") or "").strip()
            if not item_desc:
                continue
            qty = int(item.get("quantity") or 0)
            unit_price = Decimal(str(item.get("unit_price") or "0"))
            if qty <= 0 or unit_price < 0:
                continue
            line_total = unit_price * qty
            total_amount += line_total
            items.append(
                LineItem(
                    item_description=item_desc,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        if not items:
            return jsonify({"error": "All line items are empty or invalid."}), 400

        balance = total_amount - amount_paid

        tx = Transaction(
            customer_name=customer_name,
            contact=contact,
            description=description,
            total_amount=total_amount,
            amount_paid=amount_paid,
            balance=balance,
        )
        tx.items = items

        session.add(tx)
        session.commit()
        session.refresh(tx)

        return jsonify(serialize_transaction(tx)), 201
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        return jsonify({"error": "Failed to save transaction.", "details": str(exc)}), 500
    finally:
        session.close()


@app.get("/api/transactions")
def list_transactions():
    """List recent transactions and optional daily summary."""
    session = SessionLocal()
    try:
        date_str = request.args.get("date")
        query = session.query(Transaction).order_by(Transaction.created_at.desc())

        filter_date = None
        if date_str:
            try:
                filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                query = query.filter(Transaction.transaction_date == filter_date)
            except ValueError:
                filter_date = None

        transactions = query.limit(50).all()

        # Daily totals (for selected date or today)
        summary_date = filter_date or date.today()
        totals = (
            session.query(
                func.coalesce(func.sum(Transaction.total_amount), 0),
                func.coalesce(func.sum(Transaction.amount_paid), 0),
            )
            .filter(Transaction.transaction_date == summary_date)
            .one()
        )

        return jsonify(
            {
                "date": summary_date.isoformat(),
                "daily_total": float(totals[0]),
                "daily_paid": float(totals[1]),
                "transactions": [serialize_transaction(t) for t in transactions],
            }
        )
    finally:
        session.close()


@app.get("/api/transactions/<int:tx_id>")
def get_transaction(tx_id: int):
    session = SessionLocal()
    try:
        tx = session.get(Transaction, tx_id)
        if not tx:
            return jsonify({"error": "Transaction not found."}), 404
        return jsonify(serialize_transaction(tx))
    finally:
        session.close()


def serialize_transaction(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "customer_name": tx.customer_name,
        "contact": tx.contact,
        "description": tx.description,
        "total_amount": float(tx.total_amount),
        "amount_paid": float(tx.amount_paid),
        "balance": float(tx.balance),
        "created_at": tx.created_at.isoformat(),
        "transaction_date": tx.transaction_date.isoformat(),
        "items": [
            {
                "id": item.id,
                "item_description": item.item_description,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "line_total": float(item.line_total),
            }
            for item in tx.items
        ],
    }


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)



