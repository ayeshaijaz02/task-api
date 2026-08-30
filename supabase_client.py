"""
supabase_client.py

This file's only job: read your Supabase credentials from the .env file
and create ONE shared Supabase client that the rest of the app can import
and reuse. You never talk to Supabase directly anywhere else -- everything
goes through this `supabase` object.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load variables from your .env file into the environment
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY. "
        "Copy .env.example to .env and fill in your real Supabase project values."
    )

# This is the single Supabase client every route in the app will use
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)