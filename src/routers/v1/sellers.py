from typing import Annotated
from fastapi import APIRouter, Depends, Response, status, HTTPException
from icecream import ic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import IncomingSeller, ReturnedAllSellers, ReturnedSeller, ReturnedSellerData
from sqlalchemy.orm import selectinload

sellers_router = APIRouter(tags=["sellers"], prefix="/sellers")

# Больше не симулируем хранилище данных. Подключаемся к реальному, через сессию.
DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для регистрации продавца в БД. Возвращает созданного продавца.
@sellers_router.post("/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED)  # Прописываем модель ответа
async def create_seller(
    seller: IncomingSeller, session: DBSession
):
    new_seller = Seller(
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email,
        password=seller.password,
    )
    session.add(new_seller)
    await session.flush()
    return new_seller


# Ручка для получения всех продавцов 
@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    res = await session.execute(query)
    sellers = res.scalars().all()
    return {"sellers": sellers}


# Ручка для просмотра данных о конкретном продавце
@sellers_router.get("/{seller_id}", response_model=ReturnedSellerData)
async def get_seller(seller_id: int, session: DBSession):
    res = await session.execute(select(Seller).where(Seller.id == seller_id).options(selectinload(Seller.books)))
    seller = res.scalars().first()
    if seller is None:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller
    

# Ручка для удаления данных о продавце
@sellers_router.delete("/{seller_id}")
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await session.get(Seller, seller_id)
    ic(deleted_seller)
    if deleted_seller:
        await session.delete(deleted_seller)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#Ручка для обновления данных о продавце
@sellers_router.put("/{seller_id}")
async def update_seller(seller_id: int, new_data: ReturnedSeller, session: DBSession):
    if update_seller := await session.get(Seller, seller_id):
        update_seller.first_name = new_data.first_name
        update_seller.last_name = new_data.last_name
        update_seller.email = new_data.email
        await session.flush()
        return update_seller
    return Response(status_code=status.HTTP_404_NOT_FOUND)