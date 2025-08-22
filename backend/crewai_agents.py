# crewai_agents.py
from crewai import Agent

class MeetingAgents:
    def __init__(self, azure_llm):
        self.azure_llm = azure_llm

    def email_triage_agent(self, business_requirements: str):
        return Agent(
            role="Relevance Analyst",
            goal=(
                f"Decide if the email is truly about the product/service/concept '{business_requirements}', "
                "including its reasonable variations, abbreviations, informal names, and closely related references. "
                "Use context and intent, not exact string match. If clearly about the same thing: output 'YES'. "
                "If different or coincidental mention: output 'NO'."
            ),
            backstory=(
                "You are a precise email triager. Respond with 'YES' or 'NO' as the first token, "
                "optionally followed by a short rationale (one sentence)."
            ),
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )

    def meeting_agenda_extractor(self):
        return Agent(
            role="Email Thread Content Analyst",
            goal=(
                "Analyze an email thread and produce a structured report with the exact sections: "
                "Email Summaries, Meeting Agenda, Meeting Date & Time, Final Conclusion, Client Name, Product Name, Product Domain. "
                "When determining Client Name, extract ONLY the company name without any additional context, explanations, or parenthetical remarks. "
                "First check explicit mentions in the email bodies or signatures. "
                "If not clearly stated, infer the Client Name from the sender/recipient email addresses and CC fields "
                "(look for company names in domains like '@company.com' and convert them to proper names). "
                "For domain extraction examples: 'jrasoully@thehalalshack.com' should become 'The Halal Shack', "
                "'user@techifysolutions.com' should become 'Techify Solutions', '@abc-corp.com' should become 'ABC Corp'. "
                "Pay special attention to compound words and common prefixes like 'the'. "
                "If multiple possible client names appear, choose the one most relevant to the meeting context. "
                "CRITICAL: Output ONLY the company name (e.g., 'The Halal Shack', 'ABC Corp', 'Microsoft'). "
                "Do NOT add explanations like '(likely X organization)' or '(domain not stated)' or any other context. "
                "Only output 'Unknown Client' if there is truly no clear company name in either the text or email addresses. "
                "Summarize every email (chronological), extract actionable agenda items and owners, and capture all explicit or implied dates/times. "
                "Write a detailed Final Conclusion (3—6 sentences) covering outcomes, decisions, owners, and next steps. "
                "If the thread has only one email, do not use phrases like 'the first email says'—write a direct summary."
            ),
            backstory=(
                "You are a meticulous analyst specializing in email content extraction. "
                "You write concise, information-dense outputs, avoid speculation, and only infer when clearly justified by the text or metadata."
            ),
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )


    def meeting_flow_writer(self):
        """
        Agent focused ONLY on meeting flow generation from analysis data.
        No longer handles product dossier creation.
        """
        return Agent(
            role="Meeting Flow Writer",
            goal=(
                "Generate a comprehensive meeting flow document in plain text format with clear headings. "
                "Focus on meeting objectives, context, discussion points, decisions, blockers, and next steps. "
                "Use the analysis as primary source; use PRODUCT CONTEXT only to frame discussions, not invent facts. "
                "Format output as clean, professional text without markdown symbols."
            ),
            backstory=(
                "You excel at turning fragmented notes and summaries into a coherent, chronological meeting narrative. "
                "You avoid speculation and write in clear, professional prose. You focus solely on meeting flow documentation. "
                "You format output as clean, readable text without markdown formatting."
            ),
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )



    def client_dossier_creator(self, client_name: str = "", client_domain: str = ""):
        """
        Agent focused ONLY on client dossier creation.
        This will be used for creating client-specific documentation and context.
        Currently a placeholder for future implementation.
        """
        return Agent(
            role="Client Research Analyst",
            goal=(
                f"Create a comprehensive client dossier for '{client_name}' ({client_domain}). "
                "Focus on client background, industry context, business challenges, decision makers, "
                "previous interactions, and strategic positioning. Use only verified client information "
                "from the provided context. Do not invent or speculate about client details."
            ),
            backstory=(
                "You are an expert client researcher who specializes in creating detailed client profiles "
                "and strategic context documents. You focus on understanding client needs, organizational structure, "
                "and business challenges to enable more effective client engagement."
            ),
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )