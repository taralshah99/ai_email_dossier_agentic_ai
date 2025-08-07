from crewai import Agent

class MeetingAgents:
    def __init__(self, azure_llm):
        self.azure_llm = azure_llm

    def email_triage_agent(self, business_requirements: str):
        return Agent(
            role="Relevance Analyst",
            goal=(
                f"Analyze the email subject and body for relevance to the following "
                f"business requirements: '{business_requirements}'. Output 'YES' if "
                "highly relevant, 'NO' if not relevant. Consider keywords, intent, urgency, "
                "and any context in the body."
            ),
            backstory=(
                "You are a hyper-efficient routing machine. Your sole purpose is to triage "
                "emails with extreme precision. You must provide a definitive 'YES' or 'NO' "
                "based on strict relevance criteria to the provided business requirements. "
                "No other text, explanations, or punctuation are allowed."
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
