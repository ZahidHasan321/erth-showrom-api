from fastapi import Depends, HTTPException, Path, APIRouter, Body, Query
from pyairtable.api.table import Table
from utility import get_airtable_table_utility
from dependencies import get_airtable_api, AirtableApi
from config import get_settings, Settings
from pydantic import BaseModel

# Add the RecordSchema model to handle request bodies
class RecordSchema(BaseModel):
    id: str | None = None
    fields: dict

router = APIRouter(
    prefix='/airtable',
    tags=["airtable"]
)
@router.get("/{table_name}/records")
def read_airtable_records(
    table_name: str = Path(..., description="The name of the Airtable table to query."),
    api: AirtableApi = Depends(get_airtable_api), 
    settings: Settings = Depends(get_settings),
):
    """Fetches records from the dynamically specified Airtable table."""
    try:
        # 1. Manually call the utility, passing the injected resources
        table = get_airtable_table_utility(
            table_name=table_name,
            api=api,
            settings=settings
        )

        # 2. Use the resulting Table object
        records = table.all(max_records=10)

        return {
            "status": "success",
            "table_name": table.name,
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        # Handle errors during the actual data fetch
        print(f"Airtable Read Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Airtable Fetch Error: Could not read records. {e}"
        )


# --- CREATE Route ---
@router.post("/{table_name}/records")
def create_airtable_record(
    table_name: str = Path(..., description="The name of the Airtable table."),
    record_data: RecordSchema = Body(..., description="The record data to create."),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """Creates a new record in the specified Airtable table."""
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        new_record = table.create(record_data.fields, typecast=True)
        return {"status": "success", "new_record": new_record}
    except Exception as e:
        print(f"Airtable Create Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Create Error: {e}")


# --- UPDATE Route ---
@router.patch("/{table_name}/records/{record_id}")
def update_airtable_record(
    table_name: str = Path(..., description="The name of the Airtable table."),
    record_id: str = Path(..., description="The ID of the record to update."),
    record_data: RecordSchema = Body(..., description="The partial record data to update."),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """Updates an existing record in the specified Airtable table."""
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        updated_record = table.update(record_id, record_data.fields, typecast=True)
        return {"status": "success", "updated_record": updated_record}
    except Exception as e:
        print(f"Airtable Update Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Update Error: {e}")


# --- DELETE Route ---
@router.delete("/{table_name}/records/{record_id}")
def delete_airtable_record(
    table_name: str = Path(..., description="The name of the Airtable table."),
    record_id: str = Path(..., description="The ID of the record to delete."),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """Deletes a record from the specified Airtable table."""
    try:
        table = get_airtable_table_utility(table_name=table_name, api=api, settings=settings)
        deleted_record_id = table.delete(record_id)
        return {"status": "success", "deleted_record_id": deleted_record_id}
    except Exception as e:
        print(f"Airtable Delete Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Delete Error: {e}")


# --- SEARCH Route ---
@router.post("/{table_name}/search")
def search_airtable_record_route(
    table_name: str = Path(..., description="The name of the Airtable table."),
    search_fields: dict = Body(..., description='A dictionary of fields to search for. For example: {"Name": "John Doe"}'),
    api: AirtableApi = Depends(get_airtable_api),
    settings: Settings = Depends(get_settings),
):
    """Searches for a single record in the specified Airtable table using a dictionary of fields."""
    try:
        formula_parts = []
        for key, value in search_fields.items():
            formula_parts.append(f"{{{key}}} = '{value}'")
        formula = f"AND({', '.join(formula_parts)})"

        table = get_airtable_table_utility(
            table_name=table_name,
            api=api,
            settings=settings
        )
        record = table.first(formula=formula)

        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        return {"status": "success", "record": record}
    except Exception as e:
        print(f"Airtable Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Airtable Search Error: {e}")