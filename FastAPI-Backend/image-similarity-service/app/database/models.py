from pydantic import Field
from beanie import Document, PydanticObjectId
from datetime import datetime


class fvector(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    layout_code: str = Field(max_length=128)
    tenant_id: str = Field(max_length=64)
    style_type: str = Field(max_length=64)
    feature_vector: bytes
    image_url: str = Field(max_length=256)
    date_created: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "fvector"

    class config:
        schema_extra = {
            "example": {
                "id": "ObjectId",
                "layout_code": "Layout code of the style",
                "tenant_id": "Tenant ID",
                "style_type": "Type of style",
                "feature_vector": b"example_bytes",
                "image_url": "http://example.com/image.jpg",
                "date_created": datetime.now(),
            }
        }
