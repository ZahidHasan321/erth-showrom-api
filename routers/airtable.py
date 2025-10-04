from fastapi import Depends, HTTPException, Path, APIRouter, Body
from pyairtable.api.table import Table
from utility import get_airtable_table_utility
from dependencies import get_airtable_api, AirtableApi
from config import get_settings, Settings
from pydantic import BaseModel
from typing import Any, Optional


# --- Request Schema ---
class RecordSchema(BaseModel):
    id: str | None = None
    fields: dict


# --- Response Schema ---
class ApiResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
    count: Optional[int] = None


router = APIRouter(
    prefix='/airtable',
    tags=["airtable"]
)


# --- READ Route ---
@router.get("/{table_name}/records", response_model=ApiResponse)
def read_airtable_records(
    table_name: str = Path(..., description="The name of the Airtable table to query."),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        records = table.all(max_records=10)
        return ApiResponse(
            status="success",
            message=f"Fetched {len(records)} records from {table_name}",
            data=records,
            count=len(records)
        )
    except Exception as e:
        print(f"Airtable Read Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Fetch Error: {e}")


# --- GET Record by ID ---
@router.get("/{table_name}/records/{record_id}", response_model=ApiResponse)
def get_airtable_record_by_id(
    table_name: str,
    record_id: str,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        record = table.get(record_id)

        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        return ApiResponse(status="success", message="Record fetched", data=record)
    except Exception as e:
        print(f"Airtable Get by ID Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Get by ID Error: {e}")


# --- CREATE Route ---
@router.post("/{table_name}/records", response_model=ApiResponse)
def create_airtable_record(
    table_name: str,
    record_data: RecordSchema,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        new_record = table.create(record_data.fields, typecast=True)
        return ApiResponse(status="success", message="Record created", data=new_record)
    except Exception as e:
        print(f"Airtable Create Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Create Error: {e}")


# --- UPDATE Route ---
@router.patch("/{table_name}/records/{record_id}", response_model=ApiResponse)
def update_airtable_record(
    table_name: str,
    record_id: str,
    record_data: RecordSchema,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        updated_record = table.update(record_id, record_data.fields, typecast=True)
        return ApiResponse(status="success", message="Record updated", data=updated_record)
    except Exception as e:
        print(f"Airtable Update Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Update Error: {e}")


# --- DELETE Route ---
@router.delete("/{table_name}/records/{record_id}", response_model=ApiResponse)
def delete_airtable_record(
    table_name: str,
    record_id: str,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        deleted_record_id = table.delete(record_id)
        return ApiResponse(status="success", message="Record deleted", data={"deleted_record_id": deleted_record_id})
    except Exception as e:
        print(f"Airtable Delete Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Delete Error: {e}")


# --- SEARCH Route ---
@router.post("/{table_name}/search", response_model=ApiResponse)
def search_airtable_record_route(
    table_name: str,
    search_fields: dict = Body(..., description='{"Name": "John Doe"}'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        formula_parts = [f"{{{key}}} = '{value}'" for key, value in search_fields.items()]
        formula = f"AND({', '.join(formula_parts)})"

        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        record = table.first(formula=formula)

        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        return ApiResponse(status="success", message="Record found", data=record)
    except Exception as e:
        print(f"Airtable Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Search Error: {e}")
    


# --- UPSERT Route ---
@router.post("/{table_name}/upsert", response_model=ApiResponse)
def upsert_airtable_records(
    table_name: str,
    records: list[RecordSchema],
    key_fields: list[str] = Body(..., description='Fields to match existing records, e.g., ["Email"]'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """
    Upsert multiple records in Airtable: 
    - If a record with the specified key fields exists, update it.
    - If no matching record exists, create a new one.
    """
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)

        # Prepare records for upsert
        records_to_upsert = [
            {"id": record.id, "fields": record.fields} if record.id else {"fields": record.fields}
            for record in records
        ]

        # Perform the batch upsert
        upserted_records = table.batch_upsert(records_to_upsert, key_fields=key_fields)

        return ApiResponse(
            status="success",
            message=f"Upserted {len(upserted_records)} records.",
            data=upserted_records,
            count=len(upserted_records)
        )
    except Exception as e:
        print(f"Airtable Upsert Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Upsert Error: {e}")
 
@router.post("/{table_name}/search-all", response_model=ApiResponse)
def search_airtable_records(
    table_name: str,
    search_fields: dict = Body(..., description='{"Name": "John Doe"}'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        # Build formula from key/value filters
        formula_parts = [f"{{{key}}} = '{value}'" for key, value in search_fields.items()]
        formula = f"AND({', '.join(formula_parts)})" if len(formula_parts) > 1 else formula_parts[0]

        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        records = table.all(formula=formula)

        # Just return empty list if no records
        return ApiResponse(
            status="success",
            message=f"Found {len(records)} matching records",
            data=records,
            count=len(records)
        )
    except Exception as e:
        print(f"Airtable Search-All Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Search-All Error: {e}")