from fastapi import Depends, Path, APIRouter, Body
from utility import get_airtable_table_utility
from dependencies import get_airtable_api, AirtableApi
from config import get_settings, Settings
from routers.schemas import ApiResponse
from requests.exceptions import HTTPError
from typing import Optional


router = APIRouter(prefix="/airtable", tags=["orders"])


# Define table names and field names as constants
ORDER_TABLE_NAME = "ORDERS"
CUSTOMER_TABLE_NAME = "CUSTOMERS"
GARMENT_TABLE_NAME = "GARMENTS"
ORDER_ID_FIELD = "OrderID"


def fetch_order_details(
    order_record: dict, api: AirtableApi, settings: Settings
) -> dict:
    """
    Helper function to fetch customer and garment details for an order record.
    Returns a structured dict with order, customer, and garments data.
    """
    final_data = {}

    # Process Order Data (Keep Airtable format)
    final_data["order"] = {
        "id": order_record["id"],
        "createdTime": order_record.get("createdTime"),
        "fields": order_record["fields"].copy(),
    }

    # Extract linked record IDs
    order_fields = final_data["order"]["fields"]
    customer_ids = order_fields.pop("CustomerID", None)
    garment_ids = order_fields.pop("GARMENTS", None)

    # Fetch Customer Record
    final_data["customer"] = None
    if customer_ids and isinstance(customer_ids, list):
        customer_id = customer_ids[0]
        customer_table = get_airtable_table_utility(
            table_name=CUSTOMER_TABLE_NAME, api=api, settings=settings
        )
        customer_record = customer_table.get(customer_id)
        if customer_record:
            final_data["customer"] = customer_record

    # Fetch Garment Records
    final_data["garments"] = []
    if garment_ids and isinstance(garment_ids, list):
        garment_table = get_airtable_table_utility(
            table_name=GARMENT_TABLE_NAME, api=api, settings=settings
        )

        formula_parts = [f"RECORD_ID()='{gid}'" for gid in garment_ids]
        formula = f"OR({', '.join(formula_parts)})"
        garment_records = garment_table.all(formula=formula)

        final_data["garments"] = garment_records

    return final_data


# --- GET Detailed Order by OrderID (NO FLATTENING) ---
@router.get("/order_details/{order_id_value}", response_model=ApiResponse)
def get_detailed_order_by_order_id(
    order_id_value: str = Path(
        ..., description="The value of the OrderID field (e.g., 'A-1001')."
    ),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """
    1. Finds the Airtable record ID for an order using the unique field 'OrderID'.
    2. Fetches the linked Customer and Garments records.
    3. Returns the combined data, maintaining the original Airtable response structure
       (id, createdTime, fields) for all records.
    """

    try:
        # Find the Order Record ID by OrderID value
        safe_value = order_id_value.replace("'", "\\'")
        formula = f"{{{ORDER_ID_FIELD}}} = '{safe_value}'"

        order_table = get_airtable_table_utility(
            table_name=ORDER_TABLE_NAME, api=api, settings=settings
        )

        found_order_record = order_table.first(formula=formula)

        if not found_order_record:
            return ApiResponse(
                status="error",
                message=f"Order not found with {ORDER_ID_FIELD} = '{order_id_value}' in table '{ORDER_TABLE_NAME}'",
                data=None,
                count=0,
            )

        # Build the Final Response Data Structure
        final_data = fetch_order_details(found_order_record, api, settings)

        return ApiResponse(
            status="success",
            message=f"Order {order_id_value} found and details fetched (Airtable structure retained).",
            data=final_data,
            count=1,
        )

    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error",
            message="Airtable Detail Fetch Error",
            data=error_json,
            count=0,
        )

    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- GET Filtered List of Orders with Details ---
@router.post("/orders_list", response_model=ApiResponse)
def get_filtered_orders_list(
    filters: dict = Body(
        default={},
        description='Filter parameters, e.g., {"Status": "Pending", "OrderID": "A-1001"}',
    ),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """
    Fetches a list of orders based on filter parameters sent in the request body.
    For each order, it includes:
    - Order details
    - Customer details (linked)
    - Garments details (linked)

    Filters can include any order field like Status, OrderID, etc.
    Empty filters will return all orders.
    """

    try:
        # Build Airtable formula based on filters
        formula_parts = []
        for key, value in filters.items():
            if isinstance(value, bool):
                # Checkbox / boolean field
                part = f"{{{key}}}" if value else f"NOT({{{key}}})"
            elif isinstance(value, (int, float)):
                # Numeric comparison
                part = f"{{{key}}} = {value}"
            elif isinstance(value, str):
                # Exact string match
                safe_value = value.replace("'", "\\'")
                part = f"{{{key}}} = '{safe_value}'"
            else:
                # Fallback for unsupported types
                raise ValueError(
                    f"Unsupported value type for field '{key}': {type(value)}"
                )
            formula_parts.append(part)

        # Combine parts into final formula
        formula = None
        if formula_parts:
            formula = (
                f"AND({', '.join(formula_parts)})"
                if len(formula_parts) > 1
                else formula_parts[0]
            )

        # Fetch matching orders
        order_table = get_airtable_table_utility(
            table_name=ORDER_TABLE_NAME, api=api, settings=settings
        )

        # Get all orders matching the filter
        if formula:
            order_records = order_table.all(formula=formula)
        else:
            order_records = order_table.all()

        if not order_records:
            return ApiResponse(
                status="success",
                message="No orders found matching the filters",
                data=[],
                count=0,
            )

        # Fetch details for each order
        orders_with_details = []
        for order_record in order_records:
            order_details = fetch_order_details(order_record, api, settings)
            orders_with_details.append(order_details)

        return ApiResponse(
            status="success",
            message=f"Found {len(orders_with_details)} orders matching the filters",
            data=orders_with_details,
            count=len(orders_with_details),
        )

    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error",
            message="Airtable Orders List Fetch Error",
            data=error_json,
            count=0,
        )

    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )
