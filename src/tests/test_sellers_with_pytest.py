import pytest
from fastapi import status
from sqlalchemy import select

from src.models import books, sellers


# Тест на ручку создающую продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {
        "first_name": "Bruce",
        "last_name": "Wayne",
        "email": "batman@bk.ru",
        "password": "ImBatman"
    }
    response = await async_client.post("/api/v1/sellers/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()
    
    assert result_data["first_name"] == "Bruce"
    assert result_data["last_name"] == "Wayne"
    assert result_data["email"] == "batman@bk.ru"
    assert "id" in result_data
    

# Тест на ручку получения списка продавцов
@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):
    seller = sellers.Seller(first_name="Tony", last_name="Stark", email="example@bk.ru", password="IronMan")
    seller_2 = sellers.Seller(first_name="Bruce", last_name="Wayne", email="batman@example.com", password="ImBatman")
    db_session.add_all([seller, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/sellers/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["sellers"]) == 2
    assert any(
        seller["email"] == "example@bk.ru" and seller["first_name"] == "Tony" and seller["last_name"] == "Stark"
        for seller in response.json()["sellers"]
    )
    assert any(
        seller["email"] == "batman@example.com" and seller["first_name"] == "Bruce" and seller["last_name"] == "Wayne"
        for seller in response.json()["sellers"]
    )


# Тест на ручку получения одного продавца
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    seller = sellers.Seller(first_name="Tony", last_name="Stark", email="example@bk.ru", password="IronMan")
    db_session.add(seller)
    await db_session.flush()

    book = books.Book(author="Robert Martin", title="Clean Code", year=2008, count_pages=464, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/sellers/{seller.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем, что в ответе содержится информация о продавце и его книге
    assert response.json() == {
        "first_name": "Tony",
        "last_name": "Stark",
        "email": "example@bk.ru",
        "books": [
            {
                "title": "Clean Code",
                "author": "Robert Martin",
                "year": 2008,
                "id": book.id,
                "count_pages": 464,
            }
        ]
    }


# Тест на ручку удаления продавца
@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = sellers.Seller(first_name="Tony", last_name="Stark", email="example@bk.ru", password="IronMan")
    db_session.add(seller)
    await db_session.flush()

    book = books.Book(author="Robert Martin", title="Clean Code", year=2008, count_pages=464, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/sellers/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    await db_session.flush()

    all_sellers = await db_session.execute(select(sellers.Seller))
    res = all_sellers.scalars().all()
    assert len(res) == 0


# Тест на ручку обновления данных о продавце
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    seller = sellers.Seller(first_name="Tony", last_name="Stark", email="example@bk.ru", password="IronMan")
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/sellers/{seller.id}",
        json={"first_name": "Bruce", "last_name": "Wayne", "email": "batman@example.com", "password": "ImBatman", "id": seller.id},
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(sellers.Seller, seller.id)
    assert res.first_name == "Bruce"
    assert res.last_name == "Wayne"
    assert res.email == "batman@example.com"
    assert res.id == seller.id