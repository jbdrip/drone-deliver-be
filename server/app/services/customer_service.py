from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.customer import Customer
from app.schemas.api import ApiResponse
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut

def create_customer(db: Session, customer_in: CustomerCreate) -> ApiResponse:
    exists = db.query(Customer).filter(
        Customer.email == customer_in.email,
        Customer.is_active == True
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="El cliente ya existe")
    
    if customer_in.latitude is not None and not (-90 <= customer_in.latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitud fuera de rango (-90 a 90)")
    
    if customer_in.longitude is not None and not (-180 <= customer_in.longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitud fuera de rango (-180 a 180)")

    customer = Customer(
        email=customer_in.email,
        full_name=customer_in.full_name,
        phone=customer_in.phone,
        address=customer_in.address,
        latitude=customer_in.latitude,
        longitude=customer_in.longitude
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return ApiResponse(
        status="success",
        message="Cliente creado exitosamente",
        data=CustomerOut.from_orm(customer)
    )

def get_customers(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(Customer).filter(Customer.is_active == True)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter( 
            or_(
                Customer.email.ilike(search_term),
                Customer.full_name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.address.ilike(search_term)
            )
        )
        
    # Obtener el total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación después de obtener el conteo
    customers = query.offset(skip).limit(limit).all()
    customer_list = [CustomerOut.from_orm(customer) for customer in customers]

    return ApiResponse(
        status="success",
        message="Lista de clientes obtenida",
        data={
            "customers": customer_list,
            "total": total
        }
    )

def update_customer(db: Session, customer_id: str, customer_in: CustomerUpdate) -> ApiResponse:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if customer_in.latitude is not None and not (-90 <= customer_in.latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitud fuera de rango (-90 a 90)")
    
    if customer_in.longitude is not None and not (-180 <= customer_in.longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitud fuera de rango (-180 a 180)")

    update_data = customer_in.dict(exclude_unset=True, exclude_none=True)
    if update_data:
      for key, value in update_data.items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    
    return ApiResponse(
        status="success",
        message="Cliente actualizado exitosamente",
        data=CustomerOut.from_orm(customer)
    )

def deactivate_customer(db: Session, customer_id: str) -> ApiResponse:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    customer.is_active = False
    db.commit()
    db.refresh(customer)
    return ApiResponse(
        status="success",
        message="Cliente eliminado exitosamente",
        data=CustomerOut.from_orm(customer)
    )
