from pydantic import BaseModel, Field
from typing import List

class MacroStory(BaseModel):
    headline: str = Field(description="Active, punchy 1-sentence news headline.")
    context: str = Field(description="Plain English explanation of what caused this event (1-2 short sentences). Assume reader knows no industry jargon.")
    impact: str = Field(description="The concrete, real-world domino effect on prices, citizens, or markets (2 short sentences).")
    tag: str = Field(description="Single broad category word, e.g., 'Inflation', 'Trade', 'Banking', 'Fiscal', 'Energy'.")

class MicroStory(BaseModel):
    headline: str = Field(description="Clear, jargon-free 1-sentence summary of the corporate move.")
    trend: str = Field(description="What basic business principle does this show? Explain simply in 2 sentences.")
    sector: str = Field(description="Industry sector, e.g., 'Retail', 'Aviation', 'Tech', 'Pharma', 'Auto'.")

class DailyBriefingSchema(BaseModel):
    newspaper_name: str = Field(description="Name of publication extracted from header (e.g. 'Mint', 'Business Standard').")
    edition_date: str = Field(description="Date written strictly as 'DD Month YYYY' (e.g. '04 October 2026').")
    edition_city: str = Field(description="City edition name, or 'National' if generic.")
    economic_view: str = Field(description="A introductory sentence followed by 3-4 markdown bullet points weaving today's top stories into a clear, scannable narrative.")
    macro_developments: List[MacroStory] = Field(description="Exactly 2 or 3 major macroeconomic shifts.")
    micro_shifts: List[MicroStory] = Field(description="Exactly 2 or 3 major corporate/company level stories.")
    mba_concept_name: str = Field(description="One classic economics term featured in today's news (e.g., 'Liquidity', 'Deadweight Loss').")
    mba_concept_definition: str = Field(description="A textbook definition written so simply a high schooler could grasp it, tied to today's news.")
    market_pulse: str = Field(description="A single sentence declaring the market mood (Bullish, Bearish, or Cautious) and the exact reason why.")