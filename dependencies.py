from config import get_settings
from pyairtable.api import Api as AirtableApi
from functools import lru_cache

@lru_cache()
def get_airtable_api() -> AirtableApi:
    settings = get_settings() # Call the singleton function inside
    print("--- Initializing new Airtable API client ---")
    return AirtableApi(settings.AIRTABLE_API_KEY)