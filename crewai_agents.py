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
                "Analyze an email thread to extract summaries, agenda, date/time, "
                "Include each and every email's summary present in the thread."
                "final conclusion, and product details."
            ),
            backstory="You are a meticulous analyst specializing in email content extraction.",
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )

    def product_dossier_creator(self, product_name: str, product_domain: str = ""):
        return Agent(
            role="Product Research Analyst",
            goal=(
                f"Create a detailed dossier about '{product_name}', a {product_domain}. "
                "Include industry knowledge, features, benefits, use cases, and comparisons. "
                "Use internal knowledge only."
            ),
            backstory="A seasoned researcher who creates high-quality product dossiers.",
            llm=self.azure_llm,
            verbose=True,
            allow_delegation=False,
        )
