from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- User Schemas ---

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique username")
    password: str = Field(..., min_length=6, description="Plaintext password")

class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str

class WebAuthnPasskeyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    credential_id: str
    nickname: str
    sign_count: int
    transports: str
    created_at: Optional[str] = None

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: Optional[str] = None
    passkeys_count: int = 0
    passkeys: List[WebAuthnPasskeyItem] = []

# --- Metric Plugin & Component Schemas ---

class MetricDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    is_active: bool = True
    manifest: Dict[str, Any] = {}
    created_at: Optional[str] = None

class MetricPluginListResponse(BaseModel):
    success: bool = True
    plugins: List[MetricDefinitionResponse] = []

class MetricEntryCreateRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date formatted as YYYY-MM-DD")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Dynamic payload fields defined by manifest")
    notes: Optional[str] = ""

class MetricEntryUpdateRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    payload: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = ""

class MetricEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    metric_id: str
    date: str
    payload: Dict[str, Any] = {}
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MetricEntryListResponse(BaseModel):
    success: bool = True
    metric_id: Optional[str] = None
    entries: List[MetricEntryResponse] = []

# --- Legacy Entry Schemas (Backward Compatibility) ---

class EntryCreateRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date formatted as YYYY-MM-DD")
    weight: Optional[float] = None
    steps: Optional[int] = None
    notes: Optional[str] = ""

class EntryUpdateRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    weight: Optional[float] = None
    steps: Optional[int] = None
    notes: Optional[str] = ""

class EntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: str
    weight: Optional[float] = None
    steps: Optional[int] = None
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class EntryListResponse(BaseModel):
    success: bool = True
    entries: List[EntryResponse] = []

# --- Goal & Settings Schemas ---

class GoalUpdateRequest(BaseModel):
    daily_steps_goal: int = Field(default=10000, ge=1000, le=100000)
    target_weight: float = Field(default=165.0, gt=0)
    starting_weight: float = Field(default=185.0, gt=0)
    weight_unit: str = Field(default="lbs", pattern=r"^(lbs|kg|st)$")
    gemini_api_key: Optional[str] = ""

class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    daily_steps_goal: int = 10000
    target_weight: float = 165.0
    starting_weight: float = 185.0
    weight_unit: str = "lbs"
    has_gemini_api_key: bool = False
    gemini_api_key_masked: str = ""
    gemini_api_key: Optional[str] = ""
    updated_at: Optional[str] = None

# --- Stats Schema ---

class StatsData(BaseModel):
    total_days_logged: int = 0
    latest_weight: Optional[float] = None
    starting_weight: float = 185.0
    target_weight: float = 165.0
    weight_change: float = 0.0
    weight_unit: str = "lbs"
    progress_percent: float = 0.0
    today_steps: int = 0
    today_weight: Optional[float] = None
    avg_steps_7d: int = 0
    avg_steps_30d: int = 0
    best_step_day: int = 0
    total_steps: int = 0
    current_step_streak: int = 0
    days_goal_met: int = 0

class StatsResponse(BaseModel):
    success: bool = True
    stats: StatsData

# --- Scale Upload Job Schemas ---

class ScaleUploadJobItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    weight: Optional[float] = None
    unit: str = "lbs"
    date: Optional[str] = None
    time: Optional[str] = None
    error: Optional[str] = None
    notes: Optional[str] = None
    dismissed: bool = False
    created_at: Optional[str] = None

class ScaleUploadStatusResponse(BaseModel):
    success: bool = True
    jobs: List[ScaleUploadJobItem] = []
