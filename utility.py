from fastapi import Depends, HTTPException
from pyairtable.api.table import Table
from pyairtable.api import Api as AirtableApi
from config import Settings, get_settings # or settings import
from dependencies import get_airtable_api # The singleton client

def get_airtable_table_utility(
    table_name: str,
    settings: Settings = Depends(get_settings),  # Consumes cached settings
    api: AirtableApi = Depends(get_airtable_api), # Consumes singleton API
) -> Table:
    """Returns the pyairtable Table object dynamically."""
    try:
        return api.table(settings.AIRTABLE_BASE_ID, table_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Airtable Configuration Error: {e}"
        )