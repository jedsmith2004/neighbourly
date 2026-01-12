#!/usr/bin/env python
"""Add collectionDate column to order table if it doesn't exist"""
from sqlalchemy import text
from models import engine

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE "order" ADD COLUMN "collectionDate" VARCHAR'))
        conn.commit()
        print("Column 'collectionDate' added successfully!")
    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
            print("Column 'collectionDate' already exists, skipping.")
        else:
            print(f"Error: {e}")
