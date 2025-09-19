from typing import Type, TypeVar
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from bson import Binary
from .mongo_client import get_database

T = TypeVar('T', bound='BaseDocument')

class BaseDocument(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def get_collection_name(cls) -> str:
        return cls.__name__.lower() + 's'
    
    def to_mongo(self) -> dict:
        data = self.model_dump()
        # Convert UUID to string for MongoDB
        data['_id'] = str(self.id)
        data['created_at'] = self.created_at.isoformat()
        
        # Convert any other UUID fields to strings
        for key, value in data.items():
            if isinstance(value, uuid.UUID):
                data[key] = str(value)
        
        return data
    
    @classmethod
    def from_mongo(cls: Type[T], data: dict) -> T:
        if not data:
            raise ValueError("Data is empty")
        
        # Convert string back to UUID
        data['id'] = uuid.UUID(data.pop('_id'))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Convert any string UUID fields back to UUID objects
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    data[key] = uuid.UUID(value)
                except (ValueError, AttributeError):
                    pass  # Not a UUID string
        
        return cls(**data)
    
    def save(self) -> bool:
        db = get_database()
        collection = db[self.get_collection_name()]
        
        try:
            collection.insert_one(self.to_mongo())
            return True
        except Exception as e:
            print(f"Error saving document: {e}")
            return False
    
    @classmethod
    def bulk_insert(cls: Type[T], documents: list[T]) -> bool:
        db = get_database()
        collection = db[cls.get_collection_name()]
        
        try:
            # Convert all documents to MongoDB format
            mongo_docs = [doc.to_mongo() for doc in documents]
            collection.insert_many(mongo_docs)
            return True
        except Exception as e:
            print(f"Error bulk inserting documents: {e}")
            return False
    
    @classmethod
    def find_all(cls: Type[T], **filters) -> list[T]:
        db = get_database()
        collection = db[cls.get_collection_name()]
        
        try:
            results = collection.find(filters)
            return [cls.from_mongo(doc) for doc in results]
        except Exception as e:
            print(f"Error finding documents: {e}")
            return []
    
    @classmethod
    def find_one(cls: Type[T], **filters) -> T | None:
        db = get_database()
        collection = db[cls.get_collection_name()]
        
        try:
            result = collection.find_one(filters)
            return cls.from_mongo(result) if result else None
        except Exception as e:
            print(f"Error finding document: {e}")
            return None