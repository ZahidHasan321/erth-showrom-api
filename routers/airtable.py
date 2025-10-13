from fastapi import Depends, Path, APIRouter, Body
from utility import get_airtable_table_utility
from dependencies import get_airtable_api, AirtableApi
from config import get_settings, Settings
from pydantic import BaseModel
from typing import Any, Optional
from requests.exceptions import HTTPError


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


router = APIRouter(prefix="/airtable", tags=["airtable"])


# --- READ Route ---
@router.get("/{table_name}/records", response_model=ApiResponse)
def read_airtable_records(
    table_name: str = Path(..., description="The name of the Airtable table to query."),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        records = table.all(max_records=10)
        return ApiResponse(
            status="success",
            message=f"Fetched {len(records)} records from {table_name}",
            data=records,
            count=len(records),
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Read Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- GET Record by ID ---
@router.get("/{table_name}/records/{record_id}", response_model=ApiResponse)
def get_airtable_record_by_id(
    table_name: str,
    record_id: str,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        record = table.get(record_id)
        if not record:
            return ApiResponse(
                status="error", message="Record not found", data=None, count=0
            )
        return ApiResponse(
            status="success", message="Record fetched", data=record, count=1
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Get by ID Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- CREATE Route ---
@router.post("/{table_name}/records", response_model=ApiResponse)
def create_airtable_record(
    table_name: str,
    record_data: RecordSchema,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        new_record = table.create(record_data.fields, typecast=True)
        return ApiResponse(
            status="success", message="Record created", data=new_record, count=1
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Create Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


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
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        updated_record = table.update(record_id, record_data.fields, typecast=True)
        return ApiResponse(
            status="success", message="Record updated", data=updated_record, count=1
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Update Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- DELETE Route ---
@router.delete("/{table_name}/records/{record_id}", response_model=ApiResponse)
def delete_airtable_record(
    table_name: str,
    record_id: str,
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        deleted_record_id = table.delete(record_id)
        return ApiResponse(
            status="success",
            message="Record deleted",
            data={"deleted_record_id": deleted_record_id},
            count=1,
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Delete Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- SEARCH Route (first matching record) ---
@router.post("/{table_name}/search", response_model=ApiResponse)
def search_airtable_record_route(
    table_name: str,
    search_fields: dict = Body(..., description='{"Name": "John Doe"}'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        formula_parts = [
            f"{{{key}}} = '{value}'" for key, value in search_fields.items()
        ]
        formula = f"AND({', '.join(formula_parts)})"

        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )
        record = table.first(formula=formula)

        if not record:
            return ApiResponse(
                status="error", message="Record not found", data=None, count=0
            )

        return ApiResponse(
            status="success", message="Record found", data=record, count=1
        )
    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Search Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )


# --- SEARCH-ALL Route (all matching records) ---
# --- SEARCH-ALL Route (all matching records) ---
@router.post("/{table_name}/search-all", response_model=ApiResponse)
def search_airtable_records(
    table_name: str,
    search_fields: dict = Body(..., description='{"Name": "John Doe"}'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        # --------------------------------------------
        # Build Airtable formula based on value types
        # --------------------------------------------
        formula_parts = []
        for key, value in search_fields.items():
            if isinstance(value, bool):
                # ✅ Checkbox / boolean field
                part = f"{{{key}}}" if value else f"NOT({{{key}}})"
            elif isinstance(value, (int, float)):
                # ✅ Numeric comparison
                part = f"{{{key}}} = {value}"
            elif isinstance(value, str):
                # ✅ Exact string match
                # Escape single quotes inside string values
                safe_value = value.replace("'", "\\'")
                part = f"{{{key}}} = '{safe_value}'"
            else:
                # ⚠️ Fallback for unsupported types
                raise ValueError(
                    f"Unsupported value type for field '{key}': {type(value)}"
                )
            formula_parts.append(part)

        # Combine parts into final formula
        formula = (
            f"AND({', '.join(formula_parts)})"
            if len(formula_parts) > 1
            else formula_parts[0]
        )

        # --------------------------------------------
        # Perform Airtable query
        # --------------------------------------------
        table = get_airtable_table_utility(
            table_name=table_name,
            api=api,
            settings=settings,
        )

        # ✅ Fetch matching records
        records = table.all(formula=formula)

        return ApiResponse(
            status="success",
            message=f"Found {len(records)} matching records",
            data=records,
            count=len(records),
        )

    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error",
            message="Airtable Search-All Error",
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


# --- UPSERT Route ---
@router.post("/{table_name}/upsert", response_model=ApiResponse)
def upsert_airtable_records(
    table_name: str,
    records: list[RecordSchema],
    key_fields: list[str] = Body(
        ..., description='Fields to match existing records, e.g., ["Email"]'
    ),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    try:
        table = get_airtable_table_utility(
            table_name=table_name, api=api, settings=settings
        )

        records_to_upsert = [
            {"id": record.id, "fields": record.fields}
            if record.id
            else {"fields": record.fields}
            for record in records
        ]

        upserted_records = table.batch_upsert(records_to_upsert, key_fields=key_fields)

        return ApiResponse(
            status="success",
            message=f"Upserted {len(upserted_records)} records.",
            data=upserted_records,
            count=len(upserted_records),
        )

    except HTTPError as e:
        try:
            error_json = e.response.json()
        except Exception:
            error_json = {"message": str(e)}
        return ApiResponse(
            status="error", message="Airtable Upsert Error", data=error_json, count=0
        )
    except Exception as e:
        return ApiResponse(
            status="error",
            message="Unexpected server error",
            data={"error": str(e)},
            count=0,
        )
