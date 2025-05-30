from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException
from app.models.distribution_center import DistributionCenter, CenterTypeEnum
from app.schemas.api import ApiResponse
from app.schemas.distribution_center import DistributionCenterCreate, DistributionCenterUpdate, DistributionCenterOut

def create_distribution_center(db: Session, distribution_center_in: DistributionCenterCreate) -> ApiResponse:
    exists = db.query(DistributionCenter).filter(
        DistributionCenter.is_active == True,
        or_(
            DistributionCenter.name.ilike(distribution_center_in.name),
            and_(
                DistributionCenter.latitude == distribution_center_in.latitude,
                DistributionCenter.longitude == distribution_center_in.longitude
            )
        )
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ya existe una central de distribución con el mismo nombre o ubicación")
    
    if distribution_center_in.center_type not in [e.value for e in CenterTypeEnum]:
        raise HTTPException(status_code=400, detail="Tipo de central de distribución no válido")
    
    if distribution_center_in.latitude is not None and not (-90 <= distribution_center_in.latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitud fuera de rango (-90 a 90)")
    
    if distribution_center_in.longitude is not None and not (-180 <= distribution_center_in.longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitud fuera de rango (-180 a 180)")

    distribution_center = DistributionCenter(
        name=distribution_center_in.name,
        address=distribution_center_in.address,
        latitude=distribution_center_in.latitude,
        longitude=distribution_center_in.longitude,
        max_drone_range=distribution_center_in.max_drone_range,
        center_type=CenterTypeEnum(distribution_center_in.center_type)
    )
    
    db.add(distribution_center)
    db.commit()
    db.refresh(distribution_center)

    return ApiResponse(
        status="success",
        message="Central de distribución creada exitosamente",
        data=DistributionCenterOut.from_orm(distribution_center)
    )

def get_distribution_centers(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(DistributionCenter).filter(DistributionCenter.is_active == True)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                DistributionCenter.name.ilike(search_term),
                DistributionCenter.address.ilike(search_term),
                DistributionCenter.center_type.ilike(search_term)
            )
        )
        
    # Obtener el total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación después de obtener el conteo
    distribution_centers = query.offset(skip).limit(limit).all()
    distribution_center_list = [
      DistributionCenterOut.from_orm(distribution_center) for distribution_center in distribution_centers
    ]

    return ApiResponse(
        status="success",
        message="Lista de centrales de distribución obtenida",
        data={
            "distribution_centers": distribution_center_list,
            "total": total
        }
    )

def update_distribution_center(db: Session, distribution_center_id: str, distribution_center_in: DistributionCenterUpdate) -> ApiResponse:
    distribution_center = db.query(DistributionCenter).filter(DistributionCenter.id == distribution_center_id).first()
    if not distribution_center:
        raise HTTPException(status_code=404, detail="Central de distribución no encontrado")
    
    if distribution_center_in.center_type and distribution_center_in.center_type not in [e.value for e in CenterTypeEnum]:
        raise HTTPException(status_code=400, detail="Tipo de central de distribución no válido")
    
    if distribution_center_in.latitude is not None and not (-90 <= distribution_center_in.latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitud fuera de rango (-90 a 90)")
    
    if distribution_center_in.longitude is not None and not (-180 <= distribution_center_in.longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitud fuera de rango (-180 a 180)")

    update_data = distribution_center_in.dict(exclude_unset=True, exclude_none=True)
    if update_data:
      for key, value in update_data.items():
        setattr(distribution_center, key, value)
    db.commit()
    db.refresh(distribution_center)
    
    return ApiResponse(
        status="success",
        message="Central de distribución actualizada exitosamente",
        data=DistributionCenterOut.from_orm(distribution_center)
    )

def deactivate_distribution_center(db: Session, distribution_center_id: str) -> ApiResponse:
    distribution_center = db.query(DistributionCenter).filter(DistributionCenter.id == distribution_center_id).first()
    distribution_center.is_active = False
    db.commit()
    db.refresh(distribution_center)
    return ApiResponse(
        status="success",
        message="Centro de distribución eliminado exitosamente",
        data=DistributionCenterOut.from_orm(distribution_center)
    )
