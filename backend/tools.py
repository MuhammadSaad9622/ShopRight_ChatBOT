"""
Mock order database and get_order_status tool for the support agent.
"""

# Mock order database (order_id -> status and optional details)
MOCK_ORDERS = {
    "123": {"status": "Shipped", "tracking": "1Z999AA10123456784", "eta": "Feb 28, 2025"},
    "456": {"status": "Processing", "tracking": None, "eta": None},
    "789": {"status": "Delivered", "tracking": "1Z999AA10123456785", "eta": None},
    "101": {"status": "Pending", "tracking": None, "eta": None},
    "202": {"status": "Shipped", "tracking": "1Z999AA10123456786", "eta": "Mar 2, 2025"},
}


def get_order_status(order_id: str) -> dict:
    """
    Retrieve the status and details for an order by order ID.
    Use this when the user asks about order status, tracking, or delivery.
    """
    order_id = str(order_id).strip().lstrip("#")
    if order_id not in MOCK_ORDERS:
        return {
            "found": False,
            "order_id": order_id,
            "message": f"No order found with ID {order_id}. Please check the number and try again.",
        }
    data = MOCK_ORDERS[order_id].copy()
    data["found"] = True
    data["order_id"] = order_id
    return data
