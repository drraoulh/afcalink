import asyncio
import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.data.users import create_user, get_user_by_email
from app.db import get_db

async def main():
    db = get_db()
    
    # Check if we are using sqlite and initialize if needed via a simple connection 
    # (though create_user handles it)
    
    new_users = [
        ("Secrétariat & Comptabilité", "secretary@afcalink.com", "secretary"),
        ("Directeur des Admissions", "admissions@afcalink.com", "admission_director"),
        ("Directeur des Opérations", "operations@afcalink.com", "operation_director")
    ]
    
    print("--- Création des comptes administratifs ---")
    
    for full_name, email, role in new_users:
        existing = await get_user_by_email(db, email)
        if existing:
            print(f"[!] Le compte {email} existe déjà.")
            continue
            
        try:
            user_id = await create_user(
                db, 
                full_name=full_name, 
                email=email, 
                password="afcalink2024", 
                role=role
            )
            print(f"[OK] Créé : {full_name} | Rôle : {role} | ID : {user_id}")
        except Exception as e:
            print(f"[X] Erreur pour {full_name} : {e}")

    print("\nMot de passe par défaut pour tous : afcalink2024")
    print("------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
