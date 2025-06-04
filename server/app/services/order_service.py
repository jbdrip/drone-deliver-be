
import math
import heapq
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from decimal import Decimal
from app.models import Order, OrderStatus, DistributionCenter, CenterTypeEnum, Customer, Product, User
from app.schemas.api import ApiResponse
from app.schemas.order import OrderCreate, OrderUpdate, OrderOut
from app.schemas.distribution_center import DistributionCenterOut
from app.core.config import settings

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos usando la fórmula de Haversine.
    Retorna la distancia en kilómetros.
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def find_route_between_points(
    all_centers: List[DistributionCenter],
    start_center: DistributionCenter,
    target_lat: float,
    target_lon: float,
    target_center: Optional[DistributionCenter] = None
) -> Tuple[bool, List[DistributionCenter], float]:
    """
    Encuentra la ruta más corta entre un centro de inicio y un punto objetivo usando Dijkstra.
    
    Args:
        all_centers: Lista de todos los centros de distribución
        start_center: Centro de distribución de inicio
        target_lat: Latitud del objetivo
        target_lon: Longitud del objetivo
        target_center: Centro objetivo (opcional, si None el objetivo es las coordenadas)
    
    Returns:
        Tuple[bool, List[DistributionCenter], float]: 
        - bool: True si es posible llegar
        - List: Lista de centros de distribución en la ruta
        - float: Distancia total de la ruta
    """
    # Priority queue para Dijkstra: (distancia_acumulada, centro_actual, ruta_hasta_ahora)
    pq = [(0.0, start_center.id, [start_center])]
    
    # Diccionario para almacenar las distancias mínimas a cada centro
    distances = {start_center.id: 0.0}
    
    # Diccionario para mapear IDs a objetos DistributionCenter
    center_map = {center.id: center for center in all_centers}
    
    while pq:
        current_distance, current_center_id, current_route = heapq.heappop(pq)
        
        # Si ya encontramos una ruta más corta a este centro, saltamos
        if current_distance > distances.get(current_center_id, float('inf')):
            continue
            
        current_center = center_map[current_center_id]
        
        # Verificar si desde el centro actual se puede llegar al objetivo
        distance_to_target = calculate_distance(
            float(current_center.latitude),
            float(current_center.longitude),
            target_lat,
            target_lon
        )
        
        if distance_to_target <= current_center.max_drone_range:
            # ¡Podemos llegar al objetivo desde este centro!
            total_distance = current_distance + distance_to_target
            return True, current_route, total_distance
        
        # Explorar centros de distribución cercanos dentro del rango
        for next_center in all_centers:
            # Evitar ciclos y no considerar el centro actual
            if next_center.id == current_center.id:
                continue
                
            # Calcular la distancia al siguiente centro
            distance_to_next = calculate_distance(
                float(current_center.latitude),
                float(current_center.longitude),
                float(next_center.latitude),
                float(next_center.longitude)
            )
            
            # Verificar si el centro siguiente está dentro del rango del actual
            if distance_to_next <= current_center.max_drone_range:
                new_distance = current_distance + distance_to_next
                
                # Solo procesar si encontramos una ruta más corta
                if new_distance < distances.get(next_center.id, float('inf')):
                    distances[next_center.id] = new_distance
                    new_route = current_route + [next_center]
                    heapq.heappush(pq, (new_distance, next_center.id, new_route))
    
    # No se encontró una ruta válida
    return False, [], 0.0

def find_complete_delivery_route(
    db: Session,
    start_center: DistributionCenter,
    customer_lat: float,
    customer_lon: float
) -> Tuple[bool, List[DistributionCenter], float]:
    """
    Encuentra la ruta completa: Centro inicial → Bodega central → Cliente
    
    Returns:
        Tuple[bool, List[DistributionCenter], float]:
        - bool: True si es posible la entrega completa
        - List: Lista completa de centros en la ruta
        - float: Distancia total de la ruta
    """
    # Obtener todos los centros de distribución activos
    all_centers = db.query(DistributionCenter).filter(
        DistributionCenter.is_active == True
    ).all()

    # imprimir todos los centros para debugging
    print("Centros de distribución activos:")
    for center in all_centers:
        print(f"{center.name} (ID: {center.id}, Lat: {center.latitude}, Lon: {center.longitude})")
    
    # Encontrar la bodega central (main_warehouse)
    main_warehouse = db.query(DistributionCenter).filter(
        DistributionCenter.center_type == CenterTypeEnum.main_warehouse,
        DistributionCenter.is_active == True
    ).first()
    
    if not main_warehouse:
        raise HTTPException(status_code=500, detail="No se encontró la bodega central (main_warehouse)")
    
    # Si el centro de inicio ya es la bodega central, solo buscar ruta al cliente
    if start_center.id == main_warehouse.id:
        can_reach_customer, route_to_customer, distance_to_customer = find_route_between_points(
            all_centers=all_centers,
            start_center=main_warehouse,
            target_lat=customer_lat,
            target_lon=customer_lon
        )
        
        if can_reach_customer:
            return True, route_to_customer, distance_to_customer
        else:
            return False, [], 0.0
    
    # Paso 1: Buscar ruta del centro inicial a la bodega central
    can_reach_warehouse, route_to_warehouse, distance_to_warehouse = find_route_between_points(
        all_centers=all_centers,
        start_center=start_center,
        target_lat=float(main_warehouse.latitude),
        target_lon=float(main_warehouse.longitude),
        target_center=main_warehouse
    )
    
    if not can_reach_warehouse:
        return False, [], 0.0
    
    # Paso 2: Buscar ruta de la bodega central al cliente
    can_reach_customer, route_to_customer, distance_to_customer = find_route_between_points(
        all_centers=all_centers,
        start_center=main_warehouse,
        target_lat=customer_lat,
        target_lon=customer_lon
    )
    
    # Imprimir la ruta de la bodega central al cliente
    print(" -> ".join([center.name for center in route_to_customer]) + f" -> Cliente\n\n\n\n")

    if not can_reach_customer:
        return False, [], 0.0
    
    # Combinar las rutas (evitar duplicar la bodega central)
    complete_route = route_to_warehouse + route_to_customer
    total_distance = distance_to_warehouse + distance_to_customer
    
    return True, complete_route, total_distance

def find_nearest_distribution_center(
    db: Session, 
    customer_lat: float, 
    customer_lon: float
) -> Optional[DistributionCenter]:
    """
    Encuentra el centro de distribución más cercano al cliente.
    """
    # Obtener todos los centros de distribución activos
    active_centers = db.query(DistributionCenter).filter(
        DistributionCenter.is_active == True
    ).all()
    
    if not active_centers:
        return None
    
    # Inicializar variables para encontrar el centro más cercano
    nearest_center = None
    min_distance = float('inf') # Infinito para comparar distancias
    
    for center in active_centers:
        # Calcular la distancia al centro actual
        distance = calculate_distance(
            float(center.latitude),
            float(center.longitude),
            customer_lat,
            customer_lon
        )
        # Verificar si es el más cercano
        if distance < min_distance:
            min_distance = distance # Actualizar la distancia mínima
            nearest_center = center # Actualizar el centro más cercano

    # Retornar el centro más cercano encontrado
    return nearest_center

def create_order(db: Session, current_user: User, order_in: OrderCreate) -> ApiResponse:
    # Verificar si el producto existe y está activo
    product = db.query(Product).filter(
        Product.id == order_in.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado o inactivo")
    
    # Obtener al cliente asociado al usuario
    customer = db.query(Customer).filter(
        Customer.email == current_user.email,
        Customer.is_active == True
    ).first()
    
    # Encontrar el centro de distribución más cercano al cliente
    start_distribution_center = find_nearest_distribution_center(
        db=db,
        customer_lat=float(customer.latitude),
        customer_lon=float(customer.longitude)
    )
    if not start_distribution_center:
        raise HTTPException(status_code=404, detail="No hay centros de distribución activos disponibles")
    
    # Buscar la ruta completa de entrega
    can_deliver, delivery_route, total_distance = find_complete_delivery_route(
        db=db,
        start_center=start_distribution_center,
        customer_lat=float(customer.latitude),
        customer_lon=float(customer.longitude)
    )
    
    if not can_deliver:
        raise HTTPException(
            status_code=400,
            detail="No es posible entregar el pedido: no se puede establecer una ruta desde el centro asignado hacia la bodega central y/o hacia el cliente"
        )
    
    # Verificar si existe el estado de pedido "pending"
    pending_status = db.query(OrderStatus).filter(OrderStatus.status_name == "pending").first()
    if not pending_status:
        raise HTTPException(status_code=500, detail="Estado de pedido 'pending' no encontrado en la base de datos")
    
    # Calcular costos y tiempo de entrega
    product_cost = Decimal(product.price * order_in.quantity)
    service_cost = Decimal(total_distance * settings.SERVICE_COST_PER_KM)
    estimated_delivery_time = total_distance / settings.DEFAULT_DRONE_SPEED * 60  # en minutos
    
    # Crear información de la ruta para logs/debugging
    route_info = " -> ".join([center.name for center in delivery_route]) + f" -> Cliente"
    delivery_route_map = [
        {
            "center_id": str(center.id),
            "center_name": center.name,
            "latitude": float(center.latitude),
            "longitude": float(center.longitude)
        } for center in delivery_route
    ]
    delivery_route_map.append({
        "center_id": "customer",
        "center_name": "Cliente",
        "latitude": float(customer.latitude),
        "longitude": float(customer.longitude)
    })
    
    # Crear el pedido
    order = Order(
        customer_id=customer.id,
        product_id=order_in.product_id,
        quantity=order_in.quantity,
        status_id=pending_status.id,
        assigned_distribution_center_id=start_distribution_center.id,
        total_distance=round(total_distance, 2),
        service_cost=round(service_cost, 2),
        product_cost=round(product_cost, 2),
        total_cost=round(product_cost + service_cost, 2),
        estimated_delivery_time=estimated_delivery_time,
        delivery_route=delivery_route_map
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)

    # Agregar los atributos faltantes para OrderOut
    order.customer_name = customer.full_name
    order.product_name = product.name
    order.status_name = pending_status.status_name
    order.assigned_distribution_center_name = start_distribution_center.name
    
    # Crear la respuesta con los datos del pedido creado
    return ApiResponse(
        status="success",
        message=f"Pedido creado exitosamente. Centro asignado: {start_distribution_center.name}. Ruta: {route_info}",
        data={
            "order": OrderOut.from_orm(order),
            "assigned_distribution_center": DistributionCenterOut.from_orm(start_distribution_center),
            "route_info": route_info,
        }
    )

def get_orders(db: Session, current_user: User, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    # Base query con joins comunes
    base_query = db.query(
        Order.id,
        Order.customer_id,
        Customer.full_name.label('customer_name'),
        Order.product_id,
        Product.name.label('product_name'),
        Order.quantity,
        Order.status_id,
        OrderStatus.status_name,
        Order.assigned_distribution_center_id,
        DistributionCenter.name.label('assigned_distribution_center_name'),
        Order.total_distance,
        Order.service_cost,
        Order.product_cost,
        Order.total_cost,
        Order.estimated_delivery_time,
        Order.cancellation_reason,
        Order.created_at,
        Order.updated_at
    ).join(Customer, Order.customer_id == Customer.id)\
     .join(Product, Order.product_id == Product.id)\
     .join(OrderStatus, Order.status_id == OrderStatus.id)\
     .outerjoin(DistributionCenter, Order.assigned_distribution_center_id == DistributionCenter.id)
    
    # Filtrar por cliente si no es admin
    if current_user.role != "admin":
        customer = db.query(Customer).filter(
            Customer.email == current_user.email,
            Customer.is_active == True
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado o inactivo")
        
        base_query = base_query.filter(Order.customer_id == customer.id)
    
    # Aplicar búsqueda si existe
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.filter(
            or_(
                Customer.full_name.ilike(search_term),
                Product.name.ilike(search_term),
                OrderStatus.status_name.ilike(search_term),
                DistributionCenter.name.ilike(search_term)
            )
        )
    
    # Obtener total y aplicar paginación
    total = base_query.count()
    orders = base_query.offset(skip).limit(limit).all()
    
    # Convertir resultados usando _asdict() para mejor rendimiento
    order_list = [OrderOut(**order._asdict()) for order in orders]
    
    return ApiResponse(
        status="success",
        message="Pedidos obtenidos exitosamente",
        data={"total": total, "orders": order_list}
    )

def update_order(db: Session, order_id: str, order_update: OrderUpdate) -> ApiResponse:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar si el pedido se encuentra en estado "pending"
    order_status = db.query(OrderStatus).filter(OrderStatus.id == order.status_id).first()
    if order_status.status_name != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden editar pedidos en estado 'Pendiente'")

    # Update fields if provided
    if order_update.product_id is not None:
        product = db.query(Product).filter(
            Product.id == order_update.product_id,
            Product.is_active == True
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado o inactivo")
            
        order.product_id = product.id  # Actualizar id del producto
        order.product_cost = Decimal(product.price * order_update.quantity)  # Recalcular costo del producto
        order.total_cost = order.product_cost + order.service_cost  # Recalcular costo total

    db.commit()
    db.refresh(order)

    order.customer_name = ""
    order.status_name = ""
    order.product_name = product.name

    return ApiResponse(
        status="success",
        message="Pedido actualizado exitosamente",
        data=OrderOut.from_orm(order)
    )