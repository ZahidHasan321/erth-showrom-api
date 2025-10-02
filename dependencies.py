from config import get_settings
from pyairtable.api import Api as AirtableApi
from functools import lru_cache

@lru_cache()
def get_airtable_api() -> AirtableApi:
    settings = get_settings() # Call the singleton function inside
    print("--- Initializing new Airtable API client ---")
    api = AirtableApi(settings.AIRTABLE_API_KEY, retry_strategy=True)
    # base = api.bases(force=True)
    # print(base) 
    return api