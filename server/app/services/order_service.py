
import math
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models import Order, OrderStatus, DistributionCenter, CenterTypeEnum, Customer, Product
from app.schemas.api import ApiResponse
from app.schemas.order import OrderCreate, OrderUpdate, OrderOut
from collections import deque

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
    Encuentra la ruta más corta entre un centro de inicio y un punto objetivo usando BFS.
    
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
    # Cola para BFS: (centro_actual, ruta_hasta_ahora, distancia_acumulada)
    queue = deque([(start_center, [start_center], 0.0)])
    visited = set([start_center.id])
    
    # Diccionario para almacenar la mejor ruta a cada centro
    best_routes: Dict[str, Tuple[List[DistributionCenter], float]] = {
        start_center.id: ([start_center], 0.0)
    }
    
    while queue:
        current_center, current_route, current_distance = queue.popleft()
        
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
        
        # Buscar centros de distribución cercanos dentro del rango
        for next_center in all_centers:
            if next_center.id == current_center.id:
                continue
                
            distance_to_next = calculate_distance(
                float(current_center.latitude),
                float(current_center.longitude),
                float(next_center.latitude),
                float(next_center.longitude)
            )
            
            # Verificar si el centro siguiente está dentro del rango del actual
            if distance_to_next <= current_center.max_drone_range:
                new_distance = current_distance + distance_to_next
                new_route = current_route + [next_center]
                
                # Verificar si ya visitamos este centro con una ruta mejor
                if (next_center.id not in best_routes or 
                    new_distance < best_routes[next_center.id][1]):
                    
                    best_routes[next_center.id] = (new_route, new_distance)
                    
                    # Solo agregar a la cola si no hemos visitado o encontramos una ruta mejor
                    if next_center.id not in visited or new_distance < current_distance:
                        queue.append((next_center, new_route, new_distance))
                        visited.add(next_center.id)
    
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
    
    if not can_reach_customer:
        return False, [], 0.0
    
    # Combinar las rutas (evitar duplicar la bodega central)
    complete_route = route_to_warehouse + route_to_customer[1:]  # Excluir el primer elemento de route_to_customer
    total_distance = distance_to_warehouse + distance_to_customer
    
    return True, complete_route, total_distance

def calculate_service_cost(distance_km: float, num_stops: int, base_rate: float = 2.5, per_km_rate: float = 1.0, stop_fee: float = 0.5) -> float:
    """
    Calcula el costo del servicio basado en la distancia y número de paradas.
    """
    base_cost = base_rate + (distance_km * per_km_rate)
    # Fee adicional por cada parada intermedia (excluyendo el destino final)
    stop_cost = (num_stops - 1) * stop_fee if num_stops > 1 else 0
    return base_cost + stop_cost

def estimate_delivery_time(distance_km: float, num_stops: int, drone_speed_kmh: float = 50.0, stop_time_minutes: float = 5.0) -> int:
    """
    Estima el tiempo de entrega en minutos considerando paradas intermedias.
    """
    preparation_time = 10  # minutos
    flight_time = (distance_km / drone_speed_kmh) * 60  # solo ida en minutos
    # Tiempo adicional por cada parada intermedia
    stops_time = (num_stops - 1) * stop_time_minutes if num_stops > 1 else 0
    return int(preparation_time + flight_time + stops_time)

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
    
    nearest_center = None
    min_distance = float('inf')
    
    for center in active_centers:
        distance = calculate_distance(
            float(center.latitude),
            float(center.longitude),
            customer_lat,
            customer_lon
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_center = center
    
    return nearest_center

def create_order(db: Session, order_in: OrderCreate) -> ApiResponse:
    # Check if the customer exists and is active
    customer = db.query(Customer).filter(
        Customer.id == order_in.customer_id,
        Customer.is_active == True
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado o inactivo")
    
    # Check if the product exists and is active
    product = db.query(Product).filter(
        Product.id == order_in.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado o inactivo")
    
    # Find the nearest distribution center to the customer
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
    
    # Get the order status id for 'pending'
    pending_status = db.query(OrderStatus).filter(OrderStatus.status_name == "pending").first()
    if not pending_status:
        raise HTTPException(status_code=500, detail="Estado de pedido 'pending' no encontrado en la base de datos")
    
    # Calculate costs and delivery time
    product_cost = product.price * order_in.quantity
    service_cost = calculate_service_cost(total_distance, len(delivery_route))
    estimated_delivery_time = estimate_delivery_time(total_distance, len(delivery_route))
    
    # Crear información de la ruta para logs/debugging
    route_info = " -> ".join([center.name for center in delivery_route]) + f" -> Cliente"
    
    # Create a new order
    order = Order(
        customer_id=order_in.customer_id,
        product_id=order_in.product_id,
        quantity=order_in.quantity,
        status_id=pending_status.id,
        assigned_distribution_center_id=start_distribution_center.id,
        total_distance=round(total_distance, 2),
        service_cost=round(service_cost, 2),
        product_cost=product_cost,
        total_cost=product_cost + round(service_cost, 2),
        estimated_delivery_time=estimated_delivery_time,
        # Opcional: agregar campo para guardar la ruta si lo tienes en tu modelo
        # delivery_route=route_info
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Agregar información de la ruta en la respuesta
    response_data = OrderOut.from_orm(order)
    # Si OrderOut tiene campos adicionales, puedes agregar la info de la ruta
    
    return ApiResponse(
        status="success",
        message=f"Pedido creado exitosamente. Centro asignado: {start_distribution_center.name}. Ruta: {route_info}",
        data=response_data
    )

def get_orders(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(Order)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Order.customer_id.ilike(search_term),
                Order.product_id.ilike(search_term),
                Order.status_id.ilike(search_term)
            )
        )

    # Obtener el total antes de aplicar paginación
    total = query.count()

    # Aplicar paginación después de obtener el conteo
    orders = query.offset(skip).limit(limit).all()
    order_list = [OrderOut.from_orm(order) for order in orders]

    return ApiResponse(
        status="success",
        message="Pedidos obtenidos exitosamente",
        data={
            "total": total,
            "orders": order_list
        }
    )

def update_order(db: Session, order_id: str, order_update: OrderUpdate) -> ApiResponse:
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Update fields if provided
    update_order = order_update.dict(exclude_unset=True, exclude_none=True)
    if update_order:
      for key, value in update_order.items():
          setattr(order, key, value)

    db.commit()
    db.refresh(order)

    return ApiResponse(
        status="success",
        message="Pedido actualizado exitosamente",
        data=OrderOut.from_orm(order)
    )