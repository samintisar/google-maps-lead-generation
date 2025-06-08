#!/usr/bin/env python3
"""
Create test user for login testing
"""
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Organization
from auth import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.email == 'test@example.com').first()
        if not test_user:
            # Get organization
            org = db.query(Organization).first()
            if not org:
                print("No organization found. Creating default organization...")
                org = Organization(
                    name="Test Organization",
                    slug="test-org",
                    description="Test organization"
                )
                db.add(org)
                db.commit()
                db.refresh(org)
            
            # Create test user
            test_user = User(
                email='test@example.com',
                username='testuser',
                first_name='Test',
                last_name='User',
                hashed_password=get_password_hash('testpassword123'),
                organization_id=org.id,
                role='SALES_REP',
                is_active=True
            )
            db.add(test_user)
            db.commit()
            print('✅ Test user created successfully!')
            print(f'Email: test@example.com')
            print(f'Password: testpassword123')
        else:
            print('ℹ️  Test user already exists')
    except Exception as e:
        print(f'❌ Error creating test user: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 