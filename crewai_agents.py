from crewai import Agent #type:ignore

class MeetingAgents:
    def __init__(self, llm):
        self.llm = llm

    def email_triage_agent(self):
        return Agent(
            role="Relevance Analyst",
            goal=(
                "Strictly analyze an email subject for relevance to a business requirement. "
                "Your ONLY job is to output a single word: YES or NO. Nothing else."
            ),
            backstory=(
                "You are a hyper-efficient routing machine. You do not converse. You do not explain. "
                "You read a subject and a department, and you output 'YES' or 'NO'. "
                "You are evaluated on your ability to follow this single, critical instruction without fail."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def meeting_agenda_extractor(self):
        return Agent(
            role="Email Thread Content Analyst",
            goal=(
                "Analyze the full content of an email thread to extract key information: "
                "a sequential summary of each email, any meeting agendas with dates/times, a final conclusion, "
                "and the name and domain of the product being discussed."
            ),
            backstory=(
                "A meticulous analyst who specializes in dissecting email conversations. "
                "You are an expert at understanding context, identifying actionable items, and summarizing complex discussions "
                "into structured, easy-to-digest formats."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def product_dossier_creator(self, product_name: str, product_domain: str = ""):
        return Agent(
            role="Product Research Analyst",
            goal=(
                f"Create a detailed dossier about the product '{product_name}', "
                f"which is a {product_domain if product_domain else 'general product'}. "
                "The dossier should include general industry knowledge, features, benefits, potential use cases, "
                "and comparisons to similar products. Use only your internal knowledge—do not refer to external documents."
            ),
            backstory=(
                "A seasoned product research expert who crafts professional dossiers for strategic planning, "
                "sales meetings, or investor pitches. Relies solely on internal knowledge and reasoning."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

