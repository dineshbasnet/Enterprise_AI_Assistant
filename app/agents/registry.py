from .document_agent import DocumentAgent
from .knowledge_agent import KnowledgeAgent
from .support_agent import SupportAgent
from .feedback_agent import FeedbackAgent
from .conversation_agent import ConversationAgent

AGENT_REGISTRY = {
    "document": DocumentAgent(),
    "knowledge": KnowledgeAgent(),
    "support": SupportAgent(),
    "feedback": FeedbackAgent(),
    "conversational": ConversationAgent(),
    "unknown": ConversationAgent(),
}
