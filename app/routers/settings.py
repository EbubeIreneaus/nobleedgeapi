from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.settings import Setting
from app.schemas.settings import SettingUpdate, SettingResponse
from app.dependencies import get_db, require_admin
from app.models.user import User

router = APIRouter()

@router.get("/whatsapp", response_model=SettingResponse)
async def get_whatsapp_number(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == "whatsapp_number"))
    setting = result.scalars().first()
    if not setting:
        # Create a default if it doesn't exist
        setting = Setting(key="whatsapp_number", value="+10000000000", description="Company WhatsApp support number")
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    return setting

@router.put("/whatsapp", response_model=SettingResponse)
async def update_whatsapp_number(
    setting_in: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    result = await db.execute(select(Setting).where(Setting.key == "whatsapp_number"))
    setting = result.scalars().first()
    
    if not setting:
        setting = Setting(key="whatsapp_number", value=setting_in.value, description="Company WhatsApp support number")
        db.add(setting)
    else:
        setting.value = setting_in.value
    
    await db.commit()
    await db.refresh(setting)
    return setting

from app.schemas.settings import DepositAddressesUpdate, DepositAddressesResponse
from app.config import settings as app_settings

@router.get("/deposit-addresses", response_model=DepositAddressesResponse)
async def get_deposit_addresses(db: AsyncSession = Depends(get_db)):
    # Helper to get setting or fallback
    async def get_val(key: str, default: str) -> str:
        res = await db.execute(select(Setting).where(Setting.key == key))
        s = res.scalars().first()
        return s.value if s else default

    return DepositAddressesResponse(
        btc_address=await get_val("btc_deposit_address", app_settings.BTC_WALLET),
        eth_address=await get_val("eth_deposit_address", app_settings.ETH_WALLET),
        usdt_trc20_address=await get_val("usdt_trc20_deposit_address", app_settings.USDT_TRC20_WALLET),
        usdt_erc20_address=await get_val("usdt_erc20_deposit_address", app_settings.USDT_ERC20_WALLET),
        zelle_email=await get_val("zelle_deposit_address", ""),
        apple_pay_tag=await get_val("apple_pay_deposit_address", ""),
        paypal_email=await get_val("paypal_deposit_address", ""),
        bank_transfer_details=await get_val("bank_transfer_deposit_address", "")
    )

@router.put("/deposit-addresses", response_model=DepositAddressesResponse)
async def update_deposit_addresses(
    data: DepositAddressesUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    async def set_val(key: str, value: str | None):
        if value is None:
            value = ""
        res = await db.execute(select(Setting).where(Setting.key == key))
        s = res.scalars().first()
        if not s:
            s = Setting(key=key, value=value, description=f"Global {key}")
            db.add(s)
        else:
            s.value = value

    await set_val("btc_deposit_address", data.btc_address)
    await set_val("eth_deposit_address", data.eth_address)
    await set_val("usdt_trc20_deposit_address", data.usdt_trc20_address)
    await set_val("usdt_erc20_deposit_address", data.usdt_erc20_address)
    await set_val("zelle_deposit_address", data.zelle_email)
    await set_val("apple_pay_deposit_address", data.apple_pay_tag)
    await set_val("paypal_deposit_address", data.paypal_email)
    await set_val("bank_transfer_deposit_address", data.bank_transfer_details)
    
    await db.commit()
    
    return DepositAddressesResponse(
        btc_address=data.btc_address,
        eth_address=data.eth_address,
        usdt_trc20_address=data.usdt_trc20_address,
        usdt_erc20_address=data.usdt_erc20_address,
        zelle_email=data.zelle_email,
        apple_pay_tag=data.apple_pay_tag,
        paypal_email=data.paypal_email,
        bank_transfer_details=data.bank_transfer_details
    )
