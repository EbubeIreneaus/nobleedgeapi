import enum

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

class KYCStatus(str, enum.Enum):
    none = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class TransactionType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    roi_credit = "roi_credit"
    referral_bonus = "referral_bonus"
    investment = "investment"
    refund = "refund"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"

class ROICycle(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class InvestmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    paused = "paused"

class ReferralStatus(str, enum.Enum):
    pending = "pending"
    credited = "credited"
    cancelled = "cancelled"

class NotificationType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    roi = "roi"
    referral = "referral"
    system = "system"
    security = "security"
