from typing import List, Literal, Optional
from pydantic import BaseModel

# 1.2.ВХОДЯЩИЕ ДАННЫЕ:
class Message(BaseModel):
    role: Literal['player', 'reported_player', 'admin']
    text: str
    attachments: Optional[int] = 0

class IncomingTicket(BaseModel):
    kind: Literal['complaint', 'report']
    messages: List[Message]

# 1.3.ИСХОДЯЩИЕ ДАННЫЕ:
class ExtractedInfo(BaseModel):
    nickname: Optional[str] = None
    rule_refs: List[str] = []
    has_evidence: bool = False
    server: Optional[str] = None

class DraftReply(BaseModel):
    language: str
    text: str
    cited: List[str] = []

class FinalResponse(BaseModel):
    language: str
    category: str
    priority: str
    is_spam_or_duplicate: bool = False
    extracted: ExtractedInfo
    draft_reply: DraftReply
    needs_human: bool
    confidence: float
    reasons: List[str] = []
