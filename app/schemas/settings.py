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

class DepositAddressesResponse(BaseModel):
    btc_address: str
    eth_address: str
    usdt_trc20_address: str
    usdt_erc20_address: str
