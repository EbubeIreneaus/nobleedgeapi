from pydantic import BaseModel
from typing import Optional

class SettingBase(BaseModel):
    value: str

class SettingUpdate(SettingBase):
    pass

class SettingResponse(SettingBase):
    key: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class DepositAddressesUpdate(BaseModel):
    btc_address: str
    eth_address: str
    usdt_trc20_address: str
    usdt_erc20_address: str
    zelle_email: Optional[str] = None
    apple_pay_tag: Optional[str] = None
    paypal_email: Optional[str] = None
    bank_transfer_details: Optional[str] = None

class DepositAddressesResponse(BaseModel):
    btc_address: str
    eth_address: str
    usdt_trc20_address: str
    usdt_erc20_address: str
    zelle_email: Optional[str] = None
    apple_pay_tag: Optional[str] = None
    paypal_email: Optional[str] = None
    bank_transfer_details: Optional[str] = None
