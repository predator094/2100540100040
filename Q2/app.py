from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
import httpx
import uuid

app = FastAPI()

# Define base URL for e-commerce APIs
BASE_URL = "http://20.244.56.144/test/companies"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzI0MTcxMzQwLCJpYXQiOjE3MjQxNzEwNDAsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImQwYWQyMjI5LTZjYTAtNGY2NC1hZDRiLThhMjhhYTY4OGVkMyIsInN1YiI6InByZWRhdG9yYWtraTA5MDZAYmJkbml0bS5hYy5pbiJ9LCJjb21wYW55TmFtZSI6IlByZWRhdG9yIiwiY2xpZW50SUQiOiJkMGFkMjIyOS02Y2EwLTRmNjQtYWQ0Yi04YTI4YWE2ODhlZDMiLCJjbGllbnRTZWNyZXQiOiJCTGdLV1JuWFNMclVTcG9sIiwib3duZXJOYW1lIjoiQW5zaHVsIFlhZGF2Iiwib3duZXJFbWFpbCI6InByZWRhdG9yYWtraTA5MDZAYmJkbml0bS5hYy5pbiIsInJvbGxObyI6IjIxMDA1NDAxMDAwNDAifQ.weSCYUSnhMOGyq0mjqOPA9geWCuJmem0-GBj8M4JiLE"


# Utility function to generate a unique ID for products
def generate_unique_id():
    return str(uuid.uuid4())


# Utility function to fetch products from a specific e-commerce API with Bearer token
async def fetch_products(
    company: str,
    category: str,
    top: int,
    min_price: Optional[float],
    max_price: Optional[float],
):
    url = f"{BASE_URL}/{company}/categories/{category}/products"

    # Convert min_price and max_price to integers if provided
    params = {
        "top": top,
        "minPrice": int(min_price) if min_price else 0,
        "maxPrice": int(max_price) if max_price else float("inf"),
    }

    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()


# Endpoint to get top products
@app.get("/categories/{categoryname}/products")
async def get_top_products(
    categoryname: str,
    top: int = Query(10, le=100),  # Default to 10, max of 100
    minPrice: Optional[float] = None,
    maxPrice: Optional[float] = None,
    sortBy: Optional[str] = None,
    order: Optional[str] = "asc",
    page: Optional[int] = 1,
):
    if page < 1:
        raise HTTPException(status_code=400, detail="Invalid page number")

    all_products = []

    for company in ["AMZ", "FLP", "SNP", "MYN", "AZO"]:
        try:
            products = await fetch_products(
                company, categoryname, top, minPrice, maxPrice
            )
            all_products.extend(products)
        except Exception as e:
            # Log or handle the exception as needed
            print(f"Error fetching data from {company}: {e}")

    # Filter and sort products
    filtered_products = [
        p
        for p in all_products
        if (minPrice is None or p["price"] >= minPrice)
        and (maxPrice is None or p["price"] <= maxPrice)
    ]

    if sortBy:
        reverse = order == "desc"
        if sortBy in ["rating", "price", "discount"]:
            filtered_products.sort(key=lambda x: x[sortBy], reverse=reverse)
        else:
            raise HTTPException(status_code=400, detail="Invalid sortBy parameter")

    # Paginate results
    start = (page - 1) * top
    end = start + top
    paginated_products = filtered_products[start:end]

    # Add unique IDs to products
    for product in paginated_products:
        product["id"] = generate_unique_id()

    return paginated_products


# Endpoint to get product details
@app.get("/categories/products/{productId}")
async def get_product_details(productId: str):
    # In a real scenario, you would fetch the product details from the e-commerce APIs
    # Here we simulate fetching product details from the list of products

    # Fetch and combine all products for detail lookup
    all_products = []

    for company in ["AMZ", "FLP", "SNP", "MYN", "AZO"]:
        try:
            products = await fetch_products(company, "all", 100, 0, float("inf"))
            all_products.extend(products)
        except Exception as e:
            # Log or handle the exception as needed
            print(f"Error fetching data from {company}: {e}")

    for product in all_products:
        if product["id"] == productId:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
