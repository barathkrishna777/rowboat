"""Generate a comprehensive PDF report of the Rowboat project features."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)


# Colors
ORANGE = HexColor("#FF690F")
GREEN = HexColor("#1DB954")
DARK = HexColor("#192024")
GRAY = HexColor("#6B7785")
LIGHT_BG = HexColor("#FAFBFC")
LIGHT_ORANGE = HexColor("#FFF5ED")
LIGHT_GREEN = HexColor("#E8F8EE")

styles = getSampleStyleSheet()

# Custom styles
styles.add(ParagraphStyle(
    "ReportTitle", parent=styles["Title"],
    fontSize=28, textColor=ORANGE, spaceAfter=6, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "ReportSubtitle", parent=styles["Normal"],
    fontSize=14, textColor=GRAY, alignment=TA_CENTER, spaceAfter=30,
))
styles.add(ParagraphStyle(
    "SectionHead", parent=styles["Heading1"],
    fontSize=18, textColor=ORANGE, spaceBefore=24, spaceAfter=12,
    borderWidth=0, borderColor=ORANGE, borderPadding=4,
))
styles.add(ParagraphStyle(
    "SubHead", parent=styles["Heading2"],
    fontSize=14, textColor=DARK, spaceBefore=16, spaceAfter=8,
))
styles.add(ParagraphStyle(
    "BodyText2", parent=styles["Normal"],
    fontSize=11, textColor=DARK, spaceAfter=8, leading=16, alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    "BulletItem", parent=styles["Normal"],
    fontSize=11, textColor=DARK, spaceAfter=4, leading=15,
    leftIndent=20, bulletIndent=10,
))
styles.add(ParagraphStyle(
    "CodeStyle", parent=styles["Normal"],
    fontSize=9, textColor=HexColor("#333333"), fontName="Courier",
    spaceAfter=8, leftIndent=16, leading=12,
))
styles.add(ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontSize=9, textColor=GRAY, alignment=TA_CENTER, spaceAfter=12,
))
styles.add(ParagraphStyle(
    "PhaseLabel", parent=styles["Normal"],
    fontSize=12, textColor=white, fontName="Helvetica-Bold",
))
styles.add(ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=10, textColor=DARK, leading=13,
))
styles.add(ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontSize=10, textColor=white, fontName="Helvetica-Bold", leading=13,
))


def bullet(text):
    return Paragraph(f"<bullet>&bull;</bullet> {text}", styles["BulletItem"])


def sub_bullet(text):
    s = ParagraphStyle("SubBullet", parent=styles["BulletItem"], leftIndent=40, bulletIndent=30)
    return Paragraph(f"<bullet>-</bullet> {text}", s)


def build_report():
    doc = SimpleDocTemplate(
        "Rowboat_Project_Report.pdf",
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )

    story = []

    # ══════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Rowboat", styles["ReportTitle"]))
    story.append(Paragraph("AI-Powered Group Outing Planner", styles["ReportSubtitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="60%", thickness=2, color=ORANGE, spaceAfter=20))
    story.append(Spacer(1, 0.2 * inch))

    meta_data = [
        ["Course", "CMU 24-880: AI Agents for Engineers"],
        ["Team", "Barathkrishna Satheeshkumar, Naitik Khandelwal, Anushree Sabnis"],
        ["Date", "March 19, 2026"],
        ["Repository", "github.com/barathkrishna777/rowboat"],
        ["Deployment", "Railway (live)"],
    ]
    meta_table = Table(meta_data, colWidths=[1.5 * inch, 4.5 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), ORANGE),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "A multi-agent AI system that coordinates group outings end-to-end -- "
        "from collecting individual preferences to finding venues, scheduling across "
        "calendars, applying constraint-based ranking, and booking. Built with "
        "commercial product aspirations (target: Kayak-like company).",
        styles["BodyText2"],
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("Table of Contents", styles["SectionHead"]))
    toc_items = [
        "1. Executive Summary",
        "2. System Architecture",
        "3. AI Agents (PydanticAI + Gemini)",
        "4. Phase 1: Foundation",
        "5. Phase 2: Preferences, Calendar, Persistence",
        "6. Phase 2.5: UI/UX Polish",
        "7. Phase 3: Constraint Solver & RAG Pipeline",
        "8. Phase 5: Orchestrator Agent",
        "9. Tech Stack & Dependencies",
        "10. Testing & Quality",
        "11. Deployment (Railway)",
        "12. Remaining Roadmap",
        "13. Appendix: API Endpoints",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["BodyText2"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Executive Summary", styles["SectionHead"]))
    story.append(Paragraph(
        "<b>Rowboat</b> is a multi-agent AI system designed to solve the real-world problem of "
        "coordinating group outings. Planning an outing for a group involves juggling individual "
        "preferences (cuisine, activities, budget, dietary restrictions), finding matching venues, "
        "coordinating schedules across multiple people, and booking -- a process that typically "
        "involves hours of back-and-forth messaging.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "Our system uses <b>five specialized PydanticAI agents</b> powered by Google's Gemini 2.5 Flash "
        "to automate this entire workflow. Each agent handles a distinct responsibility:",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Preference Agent</b> -- Conducts an adaptive AI-driven questionnaire to build user profiles"))
    story.append(bullet("<b>Calendar Agent</b> -- Coordinates availability across group members"))
    story.append(bullet("<b>Search Agent</b> -- Searches Google Places, Yelp, Eventbrite, and Ticketmaster"))
    story.append(bullet("<b>Recommendation Agent</b> -- Applies constraint solving and RAG to rank venues"))
    story.append(bullet("<b>Orchestrator Agent</b> -- Coordinates all sub-agents autonomously for end-to-end one-click planning"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The system has been implemented through <b>Phases 1-3 and 5</b> with a polished, Kayak-inspired "
        "single-page UI, a FastAPI backend, SQLite persistence, and is deployed live on Railway.",
        styles["BodyText2"],
    ))

    # Key metrics
    metrics = [
        [Paragraph("<b>Metric</b>", styles["TableHeader"]),
         Paragraph("<b>Value</b>", styles["TableHeader"])],
        [Paragraph("AI Agents", styles["TableCell"]),
         Paragraph("5 (Preference, Calendar, Search, Recommendation, Orchestrator)", styles["TableCell"])],
        [Paragraph("External API Integrations", styles["TableCell"]),
         Paragraph("5 (Google Places, Yelp, Eventbrite, Ticketmaster, Google Maps Embed)", styles["TableCell"])],
        [Paragraph("API Endpoints", styles["TableCell"]),
         Paragraph("11 (groups, plans, preferences, calendar, recommendations, orchestrator)", styles["TableCell"])],
        [Paragraph("Test Coverage", styles["TableCell"]),
         Paragraph("69 tests, all passing", styles["TableCell"])],
        [Paragraph("Lines of Code", styles["TableCell"]),
         Paragraph("~5,750 (Python)", styles["TableCell"])],
        [Paragraph("Deployment", styles["TableCell"]),
         Paragraph("Railway (2 services: FastAPI + Streamlit)", styles["TableCell"])],
    ]
    mt = Table(metrics, colWidths=[2 * inch, 4.2 * inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 8))
    story.append(mt)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 2. SYSTEM ARCHITECTURE
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("2. System Architecture", styles["SectionHead"]))
    story.append(Paragraph(
        "The system follows a <b>layered architecture</b> with clear separation of concerns:",
        styles["BodyText2"],
    ))

    arch_data = [
        [Paragraph("<b>Layer</b>", styles["TableHeader"]),
         Paragraph("<b>Technology</b>", styles["TableHeader"]),
         Paragraph("<b>Responsibility</b>", styles["TableHeader"])],
        [Paragraph("Frontend", styles["TableCell"]),
         Paragraph("Streamlit", styles["TableCell"]),
         Paragraph("Single-page stepper UI with Kayak-inspired design", styles["TableCell"])],
        [Paragraph("Backend API", styles["TableCell"]),
         Paragraph("FastAPI", styles["TableCell"]),
         Paragraph("RESTful endpoints for groups, plans, preferences, calendar", styles["TableCell"])],
        [Paragraph("AI Agents", styles["TableCell"]),
         Paragraph("PydanticAI", styles["TableCell"]),
         Paragraph("5 specialist agents with tool-use capabilities", styles["TableCell"])],
        [Paragraph("LLM", styles["TableCell"]),
         Paragraph("Gemini 2.5 Flash", styles["TableCell"]),
         Paragraph("Primary model for all agents (via google-gla provider)", styles["TableCell"])],
        [Paragraph("Vector DB", styles["TableCell"]),
         Paragraph("ChromaDB", styles["TableCell"]),
         Paragraph("RAG knowledge base for venues and feedback", styles["TableCell"])],
        [Paragraph("Database", styles["TableCell"]),
         Paragraph("SQLite + SQLAlchemy", styles["TableCell"]),
         Paragraph("Async persistence for users, groups, events, feedback", styles["TableCell"])],
        [Paragraph("Venue APIs", styles["TableCell"]),
         Paragraph("Google Places, Yelp, Eventbrite, Ticketmaster", styles["TableCell"]),
         Paragraph("Real venue data from multiple sources", styles["TableCell"])],
        [Paragraph("Maps", styles["TableCell"]),
         Paragraph("Google Maps Embed API", styles["TableCell"]),
         Paragraph("Interactive map previews in the UI", styles["TableCell"])],
    ]
    at = Table(arch_data, colWidths=[1.2 * inch, 1.8 * inch, 3.2 * inch])
    at.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(at)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Data Flow", styles["SubHead"]))
    story.append(Paragraph(
        "User Input (UI) -> Preference Agent -> Calendar Agent -> Search Agent -> "
        "Constraint Solver + RAG -> Recommendation Agent -> Ranked Results -> "
        "Review & Book -> Feedback -> RAG Knowledge Base (loop)<br/><br/>"
        "Alternatively: User Input -> <b>Orchestrator Agent</b> (coordinates all above autonomously) -> Final Itinerary",
        styles["CodeStyle"],
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 3. AI AGENTS
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("3. AI Agents (PydanticAI + Gemini)", styles["SectionHead"]))
    story.append(Paragraph(
        "All agents use the <b>PydanticAI framework</b> with the <b>google-gla:gemini-2.5-flash</b> "
        "model. Each agent follows the lazy initialization pattern to defer API key validation "
        "until first use, preventing import-time crashes.",
        styles["BodyText2"],
    ))

    # Agent 1: Search
    story.append(Paragraph("3.1 Search Agent", styles["SubHead"]))
    story.append(Paragraph(
        "The Search Agent orchestrates venue discovery across multiple APIs. It uses PydanticAI's "
        "tool-use capability to call external services and returns structured <code>SearchResult</code> objects.",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Tools:</b> tool_search_google_places, tool_search_yelp, tool_search_eventbrite, tool_search_ticketmaster"))
    story.append(bullet("<b>Output:</b> SearchResult (venues: list[Venue], summary: str, sources_searched: list[str])"))
    story.append(bullet("<b>Strategy:</b> Always starts with Google Places (most reliable), then supplements with other sources"))
    story.append(bullet("<b>Fallback:</b> If Google Places API is unavailable, calls Gemini directly for venue recommendations"))

    # Agent 2: Preference
    story.append(Paragraph("3.2 Preference Agent", styles["SubHead"]))
    story.append(Paragraph(
        "The Preference Agent conducts an adaptive questionnaire to build rich user profiles. "
        "It generates context-aware follow-up questions based on prior answers.",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Data Collected:</b> Cuisines, activities, dietary restrictions, budget tier, dealbreakers, neighborhoods, accessibility needs, group size comfort"))
    story.append(bullet("<b>Output:</b> PreferenceExtractionResult with confidence score and missing areas"))
    story.append(bullet("<b>Adaptive:</b> Questions change based on previous answers"))

    # Agent 3: Calendar
    story.append(Paragraph("3.3 Calendar Agent", styles["SubHead"]))
    story.append(Paragraph(
        "The Calendar Agent finds time slots where all group members are available. "
        "Supports overnight scheduling (e.g., 8 PM to 2 AM wrapping to the next day).",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Tools:</b> check_user_availability, find_group_free_slots, send_calendar_invite"))
    story.append(bullet("<b>Features:</b> Date range selection, configurable time windows, minimum duration filtering"))
    story.append(bullet("<b>Output:</b> Available time slots with per-member busy/free data"))

    # Agent 4: Recommendation
    story.append(Paragraph("3.4 Recommendation Agent (Phase 3)", styles["SubHead"]))
    story.append(Paragraph(
        "The Recommendation Agent combines constraint solving with RAG-enhanced context "
        "to produce ranked, explained venue recommendations. It falls back to pure constraint "
        "scoring if the LLM is unavailable.",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Tools:</b> tool_score_and_rank_venues, tool_search_venue_knowledge_base, tool_get_past_feedback, tool_get_knowledge_base_stats"))
    story.append(bullet("<b>Output:</b> RecommendationResult (ranked_venues, rejected_venues, rag_insights, summary)"))
    story.append(bullet("<b>Fallback:</b> Pure constraint-based scoring without LLM dependency"))

    # Agent 5: Orchestrator
    story.append(Paragraph("3.5 Orchestrator Agent (Phase 5)", styles["SubHead"]))
    story.append(Paragraph(
        "The Orchestrator Agent is the \"brain\" that coordinates all sub-agents autonomously. "
        "Given a high-level natural-language request (e.g., \"Plan a bowling night for our group "
        "next weekend\"), it handles the full planning pipeline without manual step-by-step interaction.",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Pipeline:</b> Parses request -> loads group preferences -> searches venues (Search Agent) -> finds available time slots (Calendar Agent) -> ranks against constraints (Recommendation Agent) -> builds final itinerary"))
    story.append(bullet("<b>Output:</b> OrchestratorPlan (itinerary, scored_venues, available_slots, reasoning)"))
    story.append(bullet("<b>API:</b> POST /api/plans/orchestrate -- the \"one-click planning\" endpoint"))
    story.append(bullet("<b>Demonstrates:</b> True multi-agent coordination with data flow management between specialist sub-agents"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 4. PHASE 1
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Phase 1: Foundation", styles["SectionHead"]))
    # Section numbering: 4=Phase1, 5=Phase2, 6=Phase2.5, 7=Phase3, 8=Phase5(Orchestrator), 9=TechStack, 10=Testing, 11=Deployment, 12=Roadmap, 13=Appendix
    story.append(Paragraph(
        "Phase 1 established the project structure, data models, initial agent, and basic UI.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("What was built:", styles["SubHead"]))
    story.append(bullet("<b>Project Structure:</b> src/ with agents/, api/, db/, models/, tools/, ui/, rag/, constraints/"))
    story.append(bullet("<b>Data Models (Pydantic):</b> Venue, TimeSlot, Itinerary, ScoredVenue, User, Group, UserPreferences, PostEventFeedback, ConstraintSet"))
    story.append(bullet("<b>Search Agent:</b> PydanticAI agent with Yelp tool integration"))
    story.append(bullet("<b>FastAPI Backend:</b> /api/plans/search endpoint"))
    story.append(bullet("<b>Streamlit UI:</b> Basic multi-tab interface"))
    story.append(bullet("<b>Tests:</b> Model validation, Yelp tool tests"))

    # ══════════════════════════════════════════════════════════════
    # 5. PHASE 2
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Phase 2: Preferences, Calendar, Persistence", styles["SectionHead"]))

    story.append(Paragraph("5.1 Preference Collection System", styles["SubHead"]))
    story.append(bullet("Multi-select dropdowns for cuisines (Italian, Japanese, Mexican, Indian, Thai, Chinese, American, Mediterranean, Korean, Vietnamese, Ethiopian, Middle Eastern)"))
    story.append(bullet("Activity preferences (bowling, escape room, concert, karaoke, mini golf, arcade, board games, hiking, movie, comedy show, wine tasting, cooking class)"))
    story.append(bullet("Dietary restriction checkboxes (9 types including vegetarian, vegan, halal, kosher, gluten-free, nut allergy, dairy-free, shellfish allergy)"))
    story.append(bullet("Budget tier slider ($, $$, $$$, $$$$)"))
    story.append(bullet("Free-text dealbreakers and neighborhood preferences"))

    story.append(Paragraph("5.2 Calendar Coordination", styles["SubHead"]))
    story.append(bullet("Date range picker for potential outing dates"))
    story.append(bullet("Time range selection with overnight wrapping (e.g., 8 PM - 2 AM)"))
    story.append(bullet("Configurable minimum slot duration"))
    story.append(bullet("Mock calendar with simulated busy blocks for each member"))
    story.append(bullet("'Connect All Calendars' one-click button"))
    story.append(bullet("Availability algorithm that finds slots where ALL members are free"))

    story.append(Paragraph("5.3 Database Persistence", styles["SubHead"]))
    story.append(bullet("<b>SQLAlchemy async</b> with aiosqlite for non-blocking database access"))
    story.append(bullet("5 tables: users, groups, group_members, events, feedback"))
    story.append(bullet("Full CRUD operations: create/get/update users, groups, events, feedback"))
    story.append(bullet("JSON serialization for complex fields (preferences, itinerary, venue_ratings)"))

    story.append(Paragraph("5.4 Google Places Integration", styles["SubHead"]))
    story.append(bullet("Google Places API v1 TextSearch for real venue data"))
    story.append(bullet("<b>Gemini fallback:</b> When Places API is unavailable, calls Gemini directly with a structured prompt to generate venue recommendations as JSON"))
    story.append(bullet("Returns real Pittsburgh venues with addresses, ratings, categories, price tiers"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 6. PHASE 2.5
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Phase 2.5: UI/UX Polish", styles["SectionHead"]))
    story.append(Paragraph(
        "A major redesign inspired by <b>Kayak's</b> clean, bright, professional design language. "
        "The goal was to make the product feel commercial-grade, not like a class project.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("6.1 Visual Design", styles["SubHead"]))
    story.append(bullet("<b>Light theme:</b> #FAFBFC background (replacing dark mode)"))
    story.append(bullet("<b>Orange accent (#FF690F):</b> Primary actions, stepper active state, buttons"))
    story.append(bullet("<b>Green success (#1DB954):</b> Completed steps, confirmations, cuisine match badges"))
    story.append(bullet("<b>Card-based layout:</b> White cards with subtle shadows and borders"))
    story.append(bullet("Responsive 2-column layout for Review & Book step"))

    story.append(Paragraph("6.2 Single-Page Stepper Navigation", styles["SubHead"]))
    story.append(Paragraph(
        "Replaced the tab-based navigation with a <b>7-step horizontal stepper</b> embedded at the top "
        "of the page. Completing one step automatically advances to the next. Users can click "
        "completed steps to navigate backwards.",
        styles["BodyText2"],
    ))
    story.append(bullet("Steps: Create Group -> Preferences -> Calendar -> Find Venues -> Review & Book -> Booking Summary -> Feedback"))
    story.append(bullet("Active step highlighted in orange with shadow"))
    story.append(bullet("Completed steps in green with checkmark"))

    story.append(Paragraph("6.3 Smart Form Interactions", styles["SubHead"]))
    story.append(bullet("Fields clear automatically after adding group members"))
    story.append(bullet("Tab order flows naturally (Group Name -> Your Name -> Email)"))
    story.append(bullet("Counter-keyed forms to prevent Streamlit state collisions"))

    story.append(Paragraph("6.4 Venue & Slot Ranking", styles["SubHead"]))
    story.append(bullet("Card-style display matching the itinerary cards"))
    story.append(bullet("Top 3 highlighted with gold, silver, bronze left borders and medal badges"))
    story.append(bullet("Arrow buttons for reordering preferences"))
    story.append(bullet("Per-venue time slot dropdown when multiple slots available"))

    story.append(Paragraph("6.5 Review & Book Experience", styles["SubHead"]))
    story.append(bullet("<b>Left panel:</b> Ranked itinerary cards with category badges, cuisine match badges, cost estimates"))
    story.append(bullet("<b>Right panel:</b> Unified group calendar grid (all members side-by-side) with busy/free/chosen highlighting"))
    story.append(bullet("<b>Google Maps embed:</b> Interactive map showing venue location"))
    story.append(bullet("<b>Calendar legend:</b> Green = everyone free, light green = available, red = busy"))
    story.append(bullet("Click to select, preview panel updates on hover"))

    story.append(Paragraph("6.6 Booking Summary Page", styles["SubHead"]))
    story.append(bullet("Confirmation with reservation details card"))
    story.append(bullet("Cost breakdown: per-person and group total"))
    story.append(bullet("Google Maps embed for booked venue"))
    story.append(bullet("Calendar invite dispatch notification"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 7. PHASE 3
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("7. Phase 3: Constraint Solver & RAG Pipeline", styles["SectionHead"]))
    story.append(Paragraph(
        "Phase 3 adds intelligence to the recommendation pipeline through constraint-based "
        "filtering and a growing knowledge base.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("7.1 Constraint Solver", styles["SubHead"]))
    story.append(Paragraph(
        "The constraint solver evaluates each venue against the group's aggregated preferences "
        "using a two-tier system:",
        styles["BodyText2"],
    ))

    story.append(Paragraph("<b>Hard Constraints (instant reject):</b>", styles["BodyText2"]))
    story.append(bullet("<b>Budget:</b> Venue price tier must be at or below the group's strictest budget"))
    story.append(bullet("<b>Dietary:</b> Food venues must support all group members' dietary restrictions"))
    story.append(bullet("<b>Dealbreakers:</b> Keyword matching against venue name, categories, and address"))

    story.append(Paragraph("<b>Soft Constraints (weighted scoring, 0-100%):</b>", styles["BodyText2"]))
    soft_data = [
        [Paragraph("<b>Factor</b>", styles["TableHeader"]),
         Paragraph("<b>Weight</b>", styles["TableHeader"]),
         Paragraph("<b>Description</b>", styles["TableHeader"])],
        [Paragraph("Cuisine Match", styles["TableCell"]),
         Paragraph("25%", styles["TableCell"]),
         Paragraph("How well venue categories match group food preferences", styles["TableCell"])],
        [Paragraph("Activity Match", styles["TableCell"]),
         Paragraph("20%", styles["TableCell"]),
         Paragraph("How well venue matches group activity preferences", styles["TableCell"])],
        [Paragraph("Group Consensus", styles["TableCell"]),
         Paragraph("20%", styles["TableCell"]),
         Paragraph("Fraction of members whose preferences align with the venue", styles["TableCell"])],
        [Paragraph("Rating", styles["TableCell"]),
         Paragraph("15%", styles["TableCell"]),
         Paragraph("Normalized venue rating (1-5 stars -> 0-100%)", styles["TableCell"])],
        [Paragraph("Popularity", styles["TableCell"]),
         Paragraph("10%", styles["TableCell"]),
         Paragraph("Log-scaled review count as popularity proxy", styles["TableCell"])],
        [Paragraph("Neighborhood", styles["TableCell"]),
         Paragraph("10%", styles["TableCell"]),
         Paragraph("Match against preferred neighborhoods/areas", styles["TableCell"])],
    ]
    st_table = Table(soft_data, colWidths=[1.5 * inch, 0.8 * inch, 3.9 * inch])
    st_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GREEN),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#C0E0C0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(st_table)

    story.append(Paragraph("7.2 RAG Pipeline (ChromaDB)", styles["SubHead"]))
    story.append(Paragraph(
        "The RAG (Retrieval-Augmented Generation) pipeline builds a growing knowledge base "
        "that makes recommendations smarter over time.",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Venue Knowledge Base:</b> Every search indexes venue details (name, category, rating, price, address) into ChromaDB for future semantic retrieval"))
    story.append(bullet("<b>Feedback Memory:</b> Post-outing feedback (ratings, likes, dislikes) is indexed for learning"))
    story.append(bullet('<b>Semantic Search:</b> Enables natural language queries like "Find places like the bowling alley we went to last time"'))
    story.append(bullet("<b>Deduplication:</b> Venues are indexed by source + source_id to prevent duplicates"))
    story.append(bullet("<b>Metadata Filtering:</b> Supports filtering by category, minimum rating"))

    story.append(Paragraph("7.3 UI Integration", styles["SubHead"]))
    story.append(bullet("Venues <b>auto-sorted by constraint score</b> after search (best match first)"))
    story.append(bullet("Score badges on each card: green (>=70%), orange (>=40%), red (<40%)"))
    story.append(bullet("Rejected venues shown faded with violation explanation"))
    story.append(bullet("Constraint explanation text on each venue card"))
    story.append(bullet("RAG insights displayed when available"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 8. PHASE 5: ORCHESTRATOR AGENT
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("8. Phase 5: Orchestrator Agent", styles["SectionHead"]))
    story.append(Paragraph(
        "Phase 5 delivers the <b>Orchestrator Agent</b> -- a meta-agent that ties all specialist "
        "sub-agents together into a single autonomous pipeline. This is the key differentiator "
        "that transforms the system from a collection of tools into a true multi-agent system.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("8.1 Design", styles["SubHead"]))
    story.append(Paragraph(
        "The Orchestrator accepts a natural-language planning request (via the <code>QuickPlanRequest</code> "
        "model) and autonomously executes the full pipeline:",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Step 1:</b> Parse the request and load group member preferences from the database"))
    story.append(bullet("<b>Step 2:</b> Invoke the Search Agent to find matching venues"))
    story.append(bullet("<b>Step 3:</b> Invoke the Calendar Agent to find available time slots across all members"))
    story.append(bullet("<b>Step 4:</b> Build a constraint set from aggregated preferences and invoke the Recommendation Agent to score and rank venues"))
    story.append(bullet("<b>Step 5:</b> Assemble the final <code>OrchestratorPlan</code> with itinerary, reasoning, and ranked results"))

    story.append(Paragraph("8.2 API Integration", styles["SubHead"]))
    story.append(Paragraph(
        "The Orchestrator is exposed via <code>POST /api/plans/orchestrate</code>, enabling "
        "\"one-click planning\" from the UI or any API client. It returns a complete plan including "
        "scored venues, available time slots, a recommended itinerary, and the agent's reasoning.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("8.3 Testing", styles["SubHead"]))
    story.append(Paragraph(
        "The orchestrator is covered by <b>5 dedicated tests</b> in <code>test_orchestrator.py</code> "
        "validating the request/response models, dependency injection, and pipeline data flow.",
        styles["BodyText2"],
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 9. TECH STACK
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("9. Tech Stack & Dependencies", styles["SectionHead"]))

    tech_data = [
        [Paragraph("<b>Category</b>", styles["TableHeader"]),
         Paragraph("<b>Technology</b>", styles["TableHeader"]),
         Paragraph("<b>Version</b>", styles["TableHeader"])],
        [Paragraph("AI Framework", styles["TableCell"]),
         Paragraph("PydanticAI", styles["TableCell"]),
         Paragraph(">= 0.1 (output_type API)", styles["TableCell"])],
        [Paragraph("LLM", styles["TableCell"]),
         Paragraph("Google Gemini 2.5 Flash", styles["TableCell"]),
         Paragraph("via google-gla provider", styles["TableCell"])],
        [Paragraph("Backend", styles["TableCell"]),
         Paragraph("FastAPI + Uvicorn", styles["TableCell"]),
         Paragraph(">= 0.110", styles["TableCell"])],
        [Paragraph("Frontend", styles["TableCell"]),
         Paragraph("Streamlit", styles["TableCell"]),
         Paragraph(">= 1.30", styles["TableCell"])],
        [Paragraph("ORM", styles["TableCell"]),
         Paragraph("SQLAlchemy (async)", styles["TableCell"]),
         Paragraph(">= 2.0", styles["TableCell"])],
        [Paragraph("Database", styles["TableCell"]),
         Paragraph("SQLite via aiosqlite", styles["TableCell"]),
         Paragraph(">= 0.19", styles["TableCell"])],
        [Paragraph("Vector DB", styles["TableCell"]),
         Paragraph("ChromaDB", styles["TableCell"]),
         Paragraph(">= 0.4", styles["TableCell"])],
        [Paragraph("HTTP Client", styles["TableCell"]),
         Paragraph("httpx", styles["TableCell"]),
         Paragraph(">= 0.27", styles["TableCell"])],
        [Paragraph("Data Validation", styles["TableCell"]),
         Paragraph("Pydantic + pydantic-settings", styles["TableCell"]),
         Paragraph(">= 2.0", styles["TableCell"])],
        [Paragraph("Testing", styles["TableCell"]),
         Paragraph("pytest + pytest-asyncio + respx", styles["TableCell"]),
         Paragraph(">= 8.0", styles["TableCell"])],
        [Paragraph("Linting", styles["TableCell"]),
         Paragraph("Ruff", styles["TableCell"]),
         Paragraph(">= 0.3", styles["TableCell"])],
    ]
    tt = Table(tech_data, colWidths=[1.5 * inch, 2.5 * inch, 2.2 * inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tt)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 10. TESTING
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("10. Testing & Quality", styles["SectionHead"]))
    story.append(Paragraph(
        "The project maintains a comprehensive test suite with <b>69 tests</b>, all passing.",
        styles["BodyText2"],
    ))

    test_data = [
        [Paragraph("<b>Test File</b>", styles["TableHeader"]),
         Paragraph("<b>Tests</b>", styles["TableHeader"]),
         Paragraph("<b>Coverage</b>", styles["TableHeader"])],
        [Paragraph("test_constraints.py", styles["TableCell"]),
         Paragraph("27", styles["TableCell"]),
         Paragraph("Budget, dietary, dealbreaker constraints; cuisine/activity/rating/popularity/consensus scoring; full ranking", styles["TableCell"])],
        [Paragraph("test_models.py", styles["TableCell"]),
         Paragraph("15", styles["TableCell"]),
         Paragraph("All Pydantic models: User, Venue, TimeSlot, ScoredVenue, Itinerary, ConstraintSet, Feedback", styles["TableCell"])],
        [Paragraph("test_db.py", styles["TableCell"]),
         Paragraph("9", styles["TableCell"]),
         Paragraph("User CRUD, Group CRUD, Feedback save/retrieve", styles["TableCell"])],
        [Paragraph("test_orchestrator.py", styles["TableCell"]),
         Paragraph("5", styles["TableCell"]),
         Paragraph("Orchestrator models, dependency injection, pipeline data flow", styles["TableCell"])],
        [Paragraph("test_calendar.py", styles["TableCell"]),
         Paragraph("8", styles["TableCell"]),
         Paragraph("Availability algorithm, weekend slots, duration filtering, time slots", styles["TableCell"])],
        [Paragraph("test_yelp.py", styles["TableCell"]),
         Paragraph("5", styles["TableCell"]),
         Paragraph("Search, filters, details, error handling", styles["TableCell"])],
    ]
    test_t = Table(test_data, colWidths=[1.7 * inch, 0.7 * inch, 3.8 * inch])
    test_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(test_t)

    story.append(Spacer(1, 16))
    story.append(Paragraph("Key Testing Patterns:", styles["SubHead"]))
    story.append(bullet("Async tests using pytest-asyncio with auto mode"))
    story.append(bullet("HTTP mocking via respx for external API calls"))
    story.append(bullet("Monkeypatching for API key injection in tests"))
    story.append(bullet("In-memory SQLite for database tests"))

    # ══════════════════════════════════════════════════════════════
    # 11. DEPLOYMENT
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("11. Deployment (Railway)", styles["SectionHead"]))
    story.append(Paragraph(
        "The application is deployed on <b>Railway</b> with two services sharing the same GitHub repo:",
        styles["BodyText2"],
    ))
    story.append(bullet("<b>Service 1 (fantastic-determination):</b> FastAPI backend -- <code>uvicorn src.main:app --host 0.0.0.0 --port $PORT</code>"))
    story.append(bullet("<b>Service 2 (ample-nourishment):</b> Streamlit frontend -- <code>streamlit run src/ui/app.py --server.port $PORT --server.address 0.0.0.0</code>"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Environment variables managed securely via Railway's dashboard (GEMINI_API_KEY, GOOGLE_MAPS_EMBED_KEY, API_BASE). Auto-deploys on git push to main.", styles["BodyText2"]))
    story.append(Paragraph("Builder configured via railway.toml to use Nixpacks for reliable Python dependency installation.", styles["BodyText2"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # 12. ROADMAP
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph("12. Remaining Roadmap", styles["SectionHead"]))

    roadmap = [
        [Paragraph("<b>Phase</b>", styles["TableHeader"]),
         Paragraph("<b>Status</b>", styles["TableHeader"]),
         Paragraph("<b>Description</b>", styles["TableHeader"])],
        [Paragraph("Phase 1", styles["TableCell"]),
         Paragraph("COMPLETE", styles["TableCell"]),
         Paragraph("Foundation: project structure, models, search agent, API, basic UI", styles["TableCell"])],
        [Paragraph("Phase 2", styles["TableCell"]),
         Paragraph("COMPLETE", styles["TableCell"]),
         Paragraph("Preferences, calendar coordination, SQLite persistence, Google Places", styles["TableCell"])],
        [Paragraph("Phase 2.5", styles["TableCell"]),
         Paragraph("COMPLETE", styles["TableCell"]),
         Paragraph("UI/UX polish: Kayak-inspired redesign, stepper nav, interactive ranking, maps", styles["TableCell"])],
        [Paragraph("Phase 3", styles["TableCell"]),
         Paragraph("COMPLETE", styles["TableCell"]),
         Paragraph("Constraint solver (hard + soft), RAG pipeline (ChromaDB), recommendation agent", styles["TableCell"])],
        [Paragraph("Phase 4", styles["TableCell"]),
         Paragraph("PLANNED", styles["TableCell"]),
         Paragraph("Real Google Calendar OAuth + live booking integrations (OpenTable, Resy)", styles["TableCell"])],
        [Paragraph("Phase 5", styles["TableCell"]),
         Paragraph("COMPLETE", styles["TableCell"]),
         Paragraph("Orchestrator agent to coordinate all sub-agents autonomously", styles["TableCell"])],
        [Paragraph("Phase 6", styles["TableCell"]),
         Paragraph("PLANNED", styles["TableCell"]),
         Paragraph("Production hardening, deployment, analytics dashboard", styles["TableCell"])],
    ]
    rm_t = Table(roadmap, colWidths=[1 * inch, 1.1 * inch, 4.1 * inch])
    rm_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("BACKGROUND", (0, 1), (0, 5), LIGHT_GREEN),
        ("BACKGROUND", (1, 1), (1, 5), LIGHT_GREEN),
        ("BACKGROUND", (2, 1), (2, 5), LIGHT_BG),
        ("BACKGROUND", (0, 6), (-1, -1), LIGHT_ORANGE),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(rm_t)

    # ══════════════════════════════════════════════════════════════
    # 12. APPENDIX
    # ══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 20))
    story.append(Paragraph("13. Appendix: API Endpoints", styles["SectionHead"]))

    api_data = [
        [Paragraph("<b>Method</b>", styles["TableHeader"]),
         Paragraph("<b>Endpoint</b>", styles["TableHeader"]),
         Paragraph("<b>Description</b>", styles["TableHeader"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/plans/search", styles["TableCell"]),
         Paragraph("Search venues using AI search agent", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/plans/recommend", styles["TableCell"]),
         Paragraph("Score and rank venues against group constraints", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/plans/orchestrate", styles["TableCell"]),
         Paragraph("Plan an outing end-to-end using the orchestrator agent", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/groups/", styles["TableCell"]),
         Paragraph("Create a new group", styles["TableCell"])],
        [Paragraph("GET", styles["TableCell"]),
         Paragraph("/api/groups/{id}", styles["TableCell"]),
         Paragraph("Get group details", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/groups/{id}/members", styles["TableCell"]),
         Paragraph("Add member to group", styles["TableCell"])],
        [Paragraph("GET", styles["TableCell"]),
         Paragraph("/api/groups/{id}/members", styles["TableCell"]),
         Paragraph("List group members", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/preferences/{user_id}", styles["TableCell"]),
         Paragraph("Save user preferences", styles["TableCell"])],
        [Paragraph("GET", styles["TableCell"]),
         Paragraph("/api/preferences/{user_id}", styles["TableCell"]),
         Paragraph("Get user preferences", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/calendar/availability", styles["TableCell"]),
         Paragraph("Check group availability", styles["TableCell"])],
        [Paragraph("POST", styles["TableCell"]),
         Paragraph("/api/calendar/oauth/start", styles["TableCell"]),
         Paragraph("Start Google Calendar OAuth flow", styles["TableCell"])],
    ]
    api_t = Table(api_data, colWidths=[0.8 * inch, 2.5 * inch, 2.9 * inch])
    api_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(api_t)

    # Build the PDF
    doc.build(story)
    print("Report generated: Rowboat_Project_Report.pdf")


if __name__ == "__main__":
    build_report()
