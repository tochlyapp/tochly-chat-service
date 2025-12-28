from pydantic import BaseModel, Field
from typing import Dict

class SignedPreKey(BaseModel):
    key_id: int = Field(..., alias='keyId')
    public_key: str = Field(..., alias='publicKey')
    signature: str

    model_config = {
        "populate_by_name": True,
        "validate_by_name": True
    }


class PrekeyBundle(BaseModel):
    identity_key: str = Field(..., alias='identityKey')
    registration_id: int = Field(..., alias='registrationId')
    signed_prekey: SignedPreKey = Field(..., alias='signedPreKey')
    one_time_prekeys: Dict[int, str] = Field(..., alias='oneTimePreKeys')

    model_config = {
        "populate_by_name": True,
        "validate_by_name": True
    }
