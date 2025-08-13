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
                "Email Summaries, Meeting Agenda, Meeting Date & Time, Final Conclusion, Product Name, Product Domain. "
                "Summarize every email (chronological), extract actionable agenda items and owners, and capture all explicit or implied dates/times. "
                "Write a detailed Final Conclusion (3—6 sentences) covering outcomes, decisions, owners, and next steps. "
                "If the thread has only one email, do not use phrases like 'the first email says'—write a direct summary."
            ),
            backstory=(
                "You are a meticulous analyst specializing in email content extraction. "
                "You write concise, information-dense outputs, avoid speculation, and only infer when clearly justified by the text."
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
                "Generate a comprehensive meeting flow document with exact markdown headings. "
                "Focus on meeting objectives, context, discussion points, decisions, blockers, and next steps. "
                "Use the analysis as primary source; use PRODUCT CONTEXT only to frame discussions, not invent facts."
            ),
            backstory=(
                "You excel at turning fragmented notes and summaries into a coherent, chronological meeting narrative. "
                "You avoid speculation and write in clear, professional prose. You focus solely on meeting flow documentation."
            ),
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )

    def product_dossier_creator(self, product_name: str, product_domain: str = ""):
        """
        Agent focused ONLY on product dossier creation using local/internal product knowledge.
        This agent creates comprehensive product documentation from .md files.
        """
        return Agent(
            role="Product Research Analyst",
            goal=(
                f"Create a clear, professional product dossier for '{product_name}' ({product_domain}). "
                "Use ONLY the PRODUCT KNOWLEDGE included in the prompt (do not browse or invent facts). "
                "Return markdown ONLY, with the exact sections in this order:\n\n"
                "1) # Product Dossier: <Product Name>\n"
                "2) ## Executive Summary (2-4 sentences)\n"
                "3) ## Overview (short description)\n"
                "4) ## Core Features (bulleted list)\n"
                "5) ## Key Benefits (bulleted list)\n"
                "6) ## Target Users & Use Cases (bulleted list)\n"
                "7) ## Integrations & Compatibility\n"
                "8) ## Security & Compliance\n"
                "9) ## Pricing & Packaging (if present in PRODUCT KNOWLEDGE)\n"
                "10) ## Competitive Positioning & Differentiators\n"
                "11) ## Sales / Implementation Talking Points (bulleted)\n\n"
                "If some sections are not present in the PRODUCT KNOWLEDGE, write 'Not available in internal docs.' for those sections. "
                "Do NOT include placeholders for client info or speculative claims. Keep tone factual and concise."
            ),
            backstory=(
                "You are a seasoned product researcher who specializes in converting internal product documentation "
                "into crisp, comprehensive product dossiers. You focus exclusively on product features, benefits, "
                "and technical specifications without mixing in client or meeting details."
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