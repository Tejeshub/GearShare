from math import ceil
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.catalog import (
    AvailabilityStatus,
    Category,
    CreatorKit,
    CreatorKitItem,
    Equipment,
)
from app.schemas.catalog import (
    CategoryResponse,
    CreatorKitItemResponse,
    CreatorKitResponse,
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
    PaginatedResponse,
)


class CatalogService:
    @staticmethod
    def get_categories(db: Session, active_only: bool = True) -> List[CategoryResponse]:
        """Fetch categories with dynamic active product count."""
        # Query product count per category
        count_subq = (
            select(
                Equipment.category_id,
                func.count(Equipment.id).label("product_count"),
            )
            .where(Equipment.is_active == True)
            .group_by(Equipment.category_id)
            .subquery()
        )

        stmt = (
            select(
                Category,
                func.coalesce(count_subq.c.product_count, 0).label("product_count"),
            )
            .outerjoin(count_subq, Category.id == count_subq.c.category_id)
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )

        if active_only:
            stmt = stmt.where(Category.is_active == True)

        results = db.execute(stmt).all()

        responses = []
        for cat, prod_count in results:
            responses.append(
                CategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    description=cat.description,
                    is_active=cat.is_active,
                    is_visible_in_category_section=cat.is_visible_in_category_section,
                    sort_order=cat.sort_order,
                    product_count=prod_count,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )
            )
        return responses

    @staticmethod
    def get_category_by_slug(db: Session, slug: str) -> CategoryResponse:
        """Fetch a single category by slug with dynamic active product count."""
        count_stmt = (
            select(func.count(Equipment.id))
            .join(Category, Equipment.category_id == Category.id)
            .where(Category.slug == slug, Equipment.is_active == True)
        )
        prod_count = db.scalar(count_stmt) or 0

        stmt = select(Category).where(Category.slug == slug)
        cat = db.scalar(stmt)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with slug '{slug}' not found",
            )

        return CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            is_active=cat.is_active,
            is_visible_in_category_section=cat.is_visible_in_category_section,
            sort_order=cat.sort_order,
            product_count=prod_count,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        )

    @staticmethod
    def _map_equipment_to_response(item: Equipment) -> EquipmentResponse:
        return EquipmentResponse(
            id=item.product_id,
            db_id=item.id,
            name=item.name,
            brand=item.brand,
            category=item.category.name if item.category else "",
            category_slug=item.category.slug if item.category else "",
            description=item.description,
            image=item.image,
            spec=item.spec,
            specs=item.specs or [],
            price=item.price,
            availability=item.availability,
            is_featured=item.is_featured,
            is_rentable=item.is_rentable,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @classmethod
    def get_equipment_list(
        cls,
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        brand: Optional[str] = None,
        availability: Optional[AvailabilityStatus] = None,
        featured: Optional[bool] = None,
        rentable: Optional[bool] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        limit: int = 12,
        active_only: bool = True,
    ) -> PaginatedResponse[EquipmentResponse]:
        """Filtered, paginated, and sorted equipment listing."""
        query = select(Equipment).options(joinedload(Equipment.category))

        # Base active filter
        if active_only:
            query = query.where(Equipment.is_active == True)

        # Filters
        if category:
            query = query.join(Equipment.category).where(
                or_(
                    func.lower(Category.slug) == category.lower(),
                    func.lower(Category.name) == category.lower(),
                )
            )

        if brand:
            query = query.where(func.lower(Equipment.brand) == brand.lower())

        if availability:
            query = query.where(Equipment.availability == availability)

        if featured is not None:
            query = query.where(Equipment.is_featured == featured)

        if rentable is not None:
            query = query.where(Equipment.is_rentable == rentable)

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Equipment.name).like(search_pattern),
                    func.lower(Equipment.brand).like(search_pattern),
                    func.lower(Equipment.description).like(search_pattern),
                    func.lower(Equipment.spec).like(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
        total = db.scalar(count_stmt) or 0

        # Sorting
        if sort_by == "price_asc":
            query = query.order_by(Equipment.price.asc(), Equipment.name.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Equipment.price.desc(), Equipment.name.asc())
        elif sort_by == "name_asc":
            query = query.order_by(Equipment.name.asc())
        elif sort_by == "newest":
            query = query.order_by(Equipment.created_at.desc())
        else:
            # Default sorting: Name ascending
            query = query.order_by(Equipment.name.asc())

        # Pagination
        offset = (page - 1) * limit
        items = db.scalars(query.offset(offset).limit(limit)).unique().all()
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedResponse(
            items=[cls._map_equipment_to_response(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @classmethod
    def get_equipment_by_id(cls, db: Session, product_id: str) -> EquipmentResponse:
        """Fetch equipment by unique product_id/slug."""
        stmt = (
            select(Equipment)
            .options(joinedload(Equipment.category))
            .where(Equipment.product_id == product_id)
        )
        item = db.scalar(stmt)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment with ID '{product_id}' not found",
            )
        return cls._map_equipment_to_response(item)

    @classmethod
    def create_equipment(cls, db: Session, data: EquipmentCreate) -> EquipmentResponse:
        """Create new equipment product."""
        # Check duplicate product_id
        existing = db.scalar(select(Equipment).where(Equipment.product_id == data.id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Equipment with ID '{data.id}' already exists",
            )

        # Resolve category by slug or name
        cat = db.scalar(
            select(Category).where(
                or_(
                    func.lower(Category.name) == data.category.lower(),
                    func.lower(Category.slug) == data.category.lower(),
                )
            )
        )
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{data.category}' not found",
            )

        item = Equipment(
            product_id=data.id,
            name=data.name,
            brand=data.brand,
            category_id=cat.id,
            description=data.description,
            image=data.image,
            spec=data.spec,
            specs=data.specs,
            price=data.price,
            availability=data.availability,
            is_featured=data.is_featured,
            is_rentable=data.is_rentable,
            is_active=data.is_active,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return cls._map_equipment_to_response(item)

    @classmethod
    def update_equipment(
        cls, db: Session, product_id: str, data: EquipmentUpdate
    ) -> EquipmentResponse:
        """Update existing equipment."""
        stmt = (
            select(Equipment)
            .options(joinedload(Equipment.category))
            .where(Equipment.product_id == product_id)
        )
        item = db.scalar(stmt)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment with ID '{product_id}' not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "category" in update_data and update_data["category"] is not None:
            cat_val = update_data.pop("category")
            cat = db.scalar(
                select(Category).where(
                    or_(
                        func.lower(Category.name) == cat_val.lower(),
                        func.lower(Category.slug) == cat_val.lower(),
                    )
                )
            )
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{cat_val}' not found",
                )
            item.category_id = cat.id

        for key, value in update_data.items():
            setattr(item, key, value)

        db.commit()
        db.refresh(item)
        return cls._map_equipment_to_response(item)

    @staticmethod
    def delete_equipment(db: Session, product_id: str) -> None:
        """Soft delete or remove equipment."""
        stmt = select(Equipment).where(Equipment.product_id == product_id)
        item = db.scalar(stmt)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment with ID '{product_id}' not found",
            )
        db.delete(item)
        db.commit()

    @staticmethod
    def _map_kit_to_response(kit: CreatorKit) -> CreatorKitResponse:
        # Collect referenced product IDs
        product_ids = []
        for item in kit.items:
            if item.equipment and item.equipment.product_id:
                product_ids.append(item.equipment.product_id)

        return CreatorKitResponse(
            id=kit.kit_id,
            title=kit.title,
            tag=kit.tag,
            intended_use=kit.intended_use,
            description=kit.description,
            image=kit.image,
            price=kit.price,
            is_active=kit.is_active,
            sort_order=kit.sort_order,
            included_items=[
                CreatorKitItemResponse(
                    id=item.id,
                    role=item.role,
                    name=item.name,
                    quantity=item.quantity,
                    sort_order=item.sort_order,
                    product_id=item.equipment.product_id if item.equipment else None,
                )
                for item in kit.items
            ],
            product_ids=product_ids,
            created_at=kit.created_at,
            updated_at=kit.updated_at,
        )

    @classmethod
    def get_creator_kits(
        cls, db: Session, active_only: bool = True
    ) -> List[CreatorKitResponse]:
        """Fetch all creator kits with included items and linked equipment."""
        stmt = (
            select(CreatorKit)
            .options(
                joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
            )
            .order_by(CreatorKit.sort_order.asc(), CreatorKit.title.asc())
        )
        if active_only:
            stmt = stmt.where(CreatorKit.is_active == True)

        kits = db.scalars(stmt).unique().all()
        return [cls._map_kit_to_response(kit) for kit in kits]

    @classmethod
    def get_creator_kit_by_id(cls, db: Session, kit_id: str) -> CreatorKitResponse:
        """Fetch creator kit by kit_id slug."""
        stmt = (
            select(CreatorKit)
            .options(
                joinedload(CreatorKit.items).joinedload(CreatorKitItem.equipment)
            )
            .where(CreatorKit.kit_id == kit_id)
        )
        kit = db.scalar(stmt)
        if not kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Creator Kit with ID '{kit_id}' not found",
            )
        return cls._map_kit_to_response(kit)
