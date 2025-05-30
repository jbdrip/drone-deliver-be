from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.product import Product
from app.schemas.api import ApiResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

def create_product(db: Session, product_in: ProductCreate) -> ApiResponse:
    exists = db.query(Product).filter(
        Product.name.ilike(product_in.name),
        Product.is_active == True
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="Ya existe un producto con el mismo nombre")
    
    if product_in.price <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor a cero")
    
    if product_in.stock_quantity is not None and product_in.stock_quantity < 0:
        raise HTTPException(status_code=400, detail="La cantidad de stock no puede ser negativa")

    product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock_quantity=product_in.stock_quantity,
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)

    return ApiResponse(
        status="success",
        message="Producto creado exitosamente",
        data=ProductOut.from_orm(product)
    )

def get_products(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(Product).filter(Product.is_active == True)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter( 
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
        
    # Obtener el total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación después de obtener el conteo
    products = query.offset(skip).limit(limit).all()
    product_list = [ProductOut.from_orm(product) for product in products]

    return ApiResponse(
        status="success",
        message="Lista de productos obtenida",
        data={
            "products": product_list,
            "total": total
        }
    )

def update_product(db: Session, product_id: str, product_in: ProductUpdate) -> ApiResponse:
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if product_in.price is not None and product_in.price <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor a cero")
    
    if product_in.stock_quantity is not None and product_in.stock_quantity < 0:
        raise HTTPException(status_code=400, detail="La cantidad de stock no puede ser negativa")

    update_data = product_in.dict(exclude_unset=True, exclude_none=True)
    if update_data:
      for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    
    return ApiResponse(
        status="success",
        message="Producto actualizado exitosamente",
        data=ProductOut.from_orm(product)
    )

def deactivate_product(db: Session, product_id: str) -> ApiResponse:
    product = db.query(Product).filter(Product.id == product_id).first()
    product.is_active = False
    db.commit()
    db.refresh(product)
    return ApiResponse(
        status="success",
        message="Producto eliminado exitosamente",
        data=ProductOut.from_orm(product)
    )
