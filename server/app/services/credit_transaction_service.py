from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models import User, Customer, Order, CreditTransaction
from app.schemas.api import ApiResponse
from app.schemas.credit_transaction import TransactionCreate, TransactionOut
from decimal import Decimal

def create_transaction(db: Session, transaction_in: TransactionCreate) -> ApiResponse:
    
    # Verificar si el cliente existe
    customer = db.query(Customer).filter(Customer.id == transaction_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar si el usuario existe
    user = db.query(User).filter(User.id == transaction_in.credited_by_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si existe la orden si se proporciona
    if transaction_in.order_id:
        order_exists = db.query(Order).filter(Order.id == transaction_in.order_id).first()
        if not order_exists:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Validar el monto
    if transaction_in.amount <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    
    # Validar el tipo de transacción
    if transaction_in.transaction_type not in ["credit", "debit"]:
        raise HTTPException(status_code=400, detail="Tipo de transacción inválido")
    
    # Obtener el balance actual del cliente
    current_balance = customer.credit_balance

    # Calcular el nuevo balance basado en el tipo de transacción
    new_balance = current_balance
    if transaction_in.transaction_type == "credit":
        new_balance += Decimal(transaction_in.amount)
    else:
        new_balance -= Decimal(transaction_in.amount)

    # Crear la transacción
    transaction = CreditTransaction(
        customer_id=transaction_in.customer_id,
        credited_by_user_id=transaction_in.credited_by_user_id,
        amount=transaction_in.amount,
        transaction_type=transaction_in.transaction_type,
        description=transaction_in.description,
        order_id=transaction_in.order_id,
        balance_before=current_balance,
        balance_after=new_balance
    )
    
    # Agregar la transacción a la base de datos
    db.add(transaction)

    # Actualizar el balance del usuario
    customer.credit_balance = new_balance

    db.commit()
    db.refresh(transaction)
    db.refresh(customer)

    return ApiResponse(
        status="success",
        message="Transacción realizada exitosamente",
        data=TransactionOut.from_orm(transaction)
    )

def get_transactions(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(CreditTransaction)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter( 
            or_(
                CreditTransaction.transaction_type.ilike(search_term),
                CreditTransaction.description.ilike(search_term),
            )
        )
        
    # Obtener el total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación después de obtener el conteo
    transactions = query.offset(skip).limit(limit).all()
    transaction_list = [TransactionOut.from_orm(transaction) for transaction in transactions]

    return ApiResponse(
        status="success",
        message="Lista de transacciones obtenida",
        data={
            "transactions": transaction_list,
            "total": total
        }
    )
