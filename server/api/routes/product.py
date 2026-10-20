import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel

from models.database import (
    get_session,
    Product
)

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreateReq(BaseModel):
    title: str
    tenant_id: Optional[str] = "default"
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    sku: Optional[str] = None
    cover_image: Optional[str] = None
    selling_points: Optional[List[str]] = None
    stock: Optional[int] = 999

class ProductUpdateReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    sku: Optional[str] = None
    cover_image: Optional[str] = None
    selling_points: Optional[List[str]] = None
    stock: Optional[int] = None
    status: Optional[str] = None

@router.get("", response_model=List[Product])
def list_products(
    tenant_id: Optional[str] = Query("default"),
    status: Optional[str] = Query("active"),
    session: Session = Depends(get_session)
):
    query = select(Product).where(Product.tenant_id == tenant_id)
    if status:
        query = query.where(Product.status == status)
    return session.exec(query).all()

@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductCreateReq,
    session: Session = Depends(get_session)
):
    points_json = json.dumps(req.selling_points or [], ensure_ascii=False)
    prod = Product(
        title=req.title,
        tenant_id=req.tenant_id or "default",
        description=req.description,
        price=req.price,
        original_price=req.original_price,
        sku=req.sku,
        cover_image=req.cover_image,
        selling_points_json=points_json,
        stock=req.stock if req.stock is not None else 999,
        status="active"
    )
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod

@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int, session: Session = Depends(get_session)):
    prod = session.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return prod

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    req: ProductUpdateReq,
    session: Session = Depends(get_session)
):
    prod = session.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    if req.title is not None:
        prod.title = req.title
    if req.description is not None:
        prod.description = req.description
    if req.price is not None:
        prod.price = req.price
    if req.original_price is not None:
        prod.original_price = req.original_price
    if req.sku is not None:
        prod.sku = req.sku
    if req.cover_image is not None:
        prod.cover_image = req.cover_image
    if req.selling_points is not None:
        prod.selling_points_json = json.dumps(req.selling_points, ensure_ascii=False)
    if req.stock is not None:
        prod.stock = req.stock
    if req.status is not None:
        prod.status = req.status

    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod

@router.delete("/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    prod = session.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    prod.status = "archived"
    session.add(prod)
    session.commit()
    return {"status": "ok", "message": f"Product {product_id} archived"}
