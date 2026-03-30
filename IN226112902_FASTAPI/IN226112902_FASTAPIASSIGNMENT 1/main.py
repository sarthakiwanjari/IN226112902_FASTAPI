# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# --------------------------
# Sample Products Data
# --------------------------
products = [
    {"id":1, "name":"Wireless Mouse", "category":"Electronics", "price":499, "in_stock":True},
    {"id":2, "name":"Notebook", "category":"Stationery", "price":99, "in_stock":True},
    {"id":3, "name":"USB Hub", "category":"Electronics", "price":799, "in_stock":False},
    {"id":4, "name":"Pen Set", "category":"Stationery", "price":49, "in_stock":True}
]

feedback_list = []
orders = []
order_counter = 1

# --------------------------
# Task 1: Filter Products
# --------------------------
@app.get("/products/filter")
def filter_products(category: Optional[str] = None,
                    min_price: Optional[int] = None,
                    max_price: Optional[int] = None):
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    return result

# --------------------------
# Task 2: Get Product Price
# --------------------------
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    return {"error": "Product not found"}

# --------------------------
# Task 3: Customer Feedback (POST)
# --------------------------
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):
    feedback_list.append(feedback.dict())
    return {"message":"Feedback submitted successfully", "feedback": feedback, "total_feedback": len(feedback_list)}

# --------------------------
# Task 4: Product Summary Dashboard
# --------------------------
@app.get("/products/summary")
def product_summary():
    total_products = len(products)
    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = total_products - in_stock_count
    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])
    categories = list(set([p["category"] for p in products]))
    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# --------------------------
# Task 5: Bulk Orders (POST)
# --------------------------
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    global order_counter
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
            grand_total += subtotal
    orders.append({
        "order_id": order_counter,
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total,
        "status": "pending"
    })
    order_counter += 1
    return orders[-1]

# --------------------------
# Bonus: Order Status Tracker
# --------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order = next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    return order

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    order = next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    order["status"] = "confirmed"
    return order