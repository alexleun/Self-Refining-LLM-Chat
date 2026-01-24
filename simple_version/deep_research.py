import requests
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    PLANNING = "planning"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    REPORTING = "reporting"
    REFLECTING = "reflecting"
    CHART_GENERATING = "chart_generating"


@dataclass
class MermaidChart:
    title: str
    chart_type: str
    code: str
    description: str


@dataclass
class ResearchReport:
    title: str
    executive_summary: str
    sections: List[Dict[str, str]]
    sources: List[Dict[str, str]]
    methodology: str
    confidence_score: float
    limitations: List[str]
    suggested_followup: List[str]
    charts: List[MermaidChart] = field(default_factory=list)
    query: str = ""
    generated_at: str = ""
    filepath: str = ""


class LMStudioClient:
    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1/chat/completions"):
        self.base_url = base_url
        self.model = None
        self._identify_model()

    def _identify_model(self):
        try:
            response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json().get("data", [])
                if models:
                    self.model = models[0].get("id", "unknown")
                    logger.info(f"Identified model: {self.model}")
        except Exception as e:
            logger.warning(f"Could not identify model: {e}")
            self.model = "local-model"

    def complete(self, messages: List[Dict[str, str]], system_prompt: str = None, 
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        headers = {"Content-Type": "application/json"}
        
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=1200)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            raise


class SearXNGClient:
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url.rstrip('/')
        self.search_url = f"{self.base_url}/search"

    def search(self, query: str, categories: List[str] = None, language: str = "en",
               num_results: int = 10) -> List[Dict[str, Any]]:
        params = {
            "q": query,
            "format": "json",
            "language": language,
            "engines": ",".join(categories) if categories else "general",
        }

        try:
            response = requests.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])[:num_results]
            
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "engine": r.get("engine", ""),
                    "published_date": r.get("publishedDate", None)
                })
            
            logger.info(f"Found {len(formatted_results)} results for: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"SearXNG search failed: {e}")
            return []


class DeepResearcher:
    def __init__(self, llm_client: LMStudioClient, search_client: SearXNGClient):
        self.llm = llm_client
        self.search = search_client
        self.research_history = []
        self.iteration_count = 0

    def generate_system_prompt(self, phase: ResearchPhase, context: Dict = None) -> str:
        base_prompt = """You are an expert research assistant with advanced analytical capabilities.
Your goal is to conduct thorough, accurate, and comprehensive research on user queries.
You always verify information from multiple sources when possible.
You acknowledge uncertainty and limitations in your knowledge.
You provide well-structured, actionable reports."""

        phase_prompts = {
            ResearchPhase.PLANNING: """
You are in the PLANNING phase. Analyze the research query and develop a strategic research plan.
Consider:
- What are the key concepts and dimensions of the query?
- What information sources would be most valuable?
- What search strategies would yield the best results?
- What is the logical structure for the final report?

Output a JSON object with:
- "research_plan": list of research questions to investigate
- "search_queries": list of search queries in priority order
- "key_concepts": list of essential concepts to explore
- "estimated_depth": low/medium/high
""",
            ResearchPhase.SEARCHING: """
You are in the SEARCHING phase. Formulate effective search queries based on the research plan.
Consider:
- Use specific, targeted queries
- Include alternative phrasings and synonyms
- Consider time-sensitive aspects if relevant
- Balance specificity with breadth

Output a JSON object with:
- "queries": list of refined search queries
- "rationale": brief explanation of query strategy
- "priority_order": reasoning for search order
""",
            ResearchPhase.ANALYZING: """
You are in the ANALYZING phase. Synthesize findings from multiple sources.
Consider:
- Identify key themes and patterns
- Note agreements and contradictions between sources
- Assess credibility and reliability
- Extract actionable insights

Output a JSON object with:
- "key_findings": list of main discoveries
- "themes": recurring topics across sources
- "conflicts": any contradictions found
- "credibility_notes": source quality observations
- "data_gaps": missing information areas
""",
            ResearchPhase.SYNTHESIZING: """
You are in the SYNTHESIZING phase. Combine findings into a coherent narrative.
Consider:
- How do the pieces connect?
- What is the overall picture?
- What conclusions can be drawn?
- What remains uncertain?

Output a JSON object with:
- "main_thesis": central finding or argument
- "supporting_evidence": key evidence categories
- "counter_points": limitations or opposing views
- "confidence_assessment": confidence level (0-1)
- "narrative_outline": structure for the report
""",
            ResearchPhase.REPORTING: """
You are in the REPORTING phase. Generate a comprehensive research report.
Structure the report with:
1. Executive Summary
2. Introduction and Context
3. Key Findings (with subsections)
4. Analysis and Discussion
5. Conclusions and Implications
6. Limitations and Caveats
7. Suggested Further Research

Output a JSON object with:
- "title": report title
- "executive_summary": 2-3 paragraph summary
- "sections": list of {heading, content} pairs
- "methodology": brief description of research approach
- "confidence_score": 0-1 scale
- "limitations": list of research limitations
- "suggested_followup": list of follow-up research areas
""",
            ResearchPhase.REFLECTING: """
You are in the REFLECTING phase. Evaluate the research process and identify improvements.
Consider:
- What worked well?
- What could be improved?
- Are there gaps in the research?
- What would you do differently?

Output a JSON object with:
- "strengths": what went well
- "weaknesses": areas for improvement
- "lessons_learned": key takeaways for future research
- "improvement_suggestions": specific enhancements
- "self_assessment": quality score (0-1)
"""
        }

        prompt = base_prompt + phase_prompts.get(phase, "")
        
        if context:
            prompt += f"\n\nCurrent context:\n{json.dumps(context, indent=2)}"
        
        return prompt

    def execute_research(self, query: str, max_iterations: int = 5, save_path: Optional[str] = None) -> ResearchReport:
        logger.info(f"Starting deep research on: {query}")
        
        context = {"original_query": query}
        
        for self.iteration_count in range(1, max_iterations + 1):
            logger.info(f"Iteration {self.iteration_count}/{max_iterations}")
            
            try:
                phase = ResearchPhase.PLANNING if self.iteration_count == 1 else ResearchPhase.ANALYZING
                
                if self.iteration_count == 1:
                    plan = self._execute_phase(phase, context)
                    context["research_plan"] = plan
                    
                    searches = self._execute_phase(ResearchPhase.SEARCHING, context)
                    context["search_results"] = []
                    
                    for search_query in searches.get("queries", []):
                        results = self.search.search(search_query, num_results=10)
                        context["search_results"].append({
                            "query": search_query,
                            "results": results
                        })
                        time.sleep(1)
                
                analysis = self._execute_phase(ResearchPhase.ANALYZING, context)
                context["analysis"] = analysis
                
                synthesis = self._execute_phase(ResearchPhase.SYNTHESIZING, context)
                context["synthesis"] = synthesis
                
                if self.iteration_count == max_iterations:
                    report_data = self._execute_phase(ResearchPhase.REPORTING, context)
                    
                    reflection = self._execute_phase(ResearchPhase.REFLECTING, {"report": report_data, "full_context": context})
                    
                    sections = report_data.get("sections", [])
                    
                    logger.info("Generating Mermaid charts for suitable content...")
                    charts = self._generate_charts_for_report(sections)
                    
                    report = ResearchReport(
                        title=report_data.get("title", "Research Report"),
                        executive_summary=report_data.get("executive_summary", ""),
                        sections=sections,
                        sources=self._extract_sources(context),
                        methodology=report_data.get("methodology", "Web search and LLM analysis"),
                        confidence_score=report_data.get("confidence_score", 0.5),
                        limitations=report_data.get("limitations", []),
                        suggested_followup=report_data.get("suggested_followup", []),
                        charts=charts,
                        query=query,
                        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    
                    if save_path:
                        filepath = self.save_report_to_markdown(report, save_path)
                        report.filepath = filepath
                    
                    return report
                
            except Exception as e:
                logger.error(f"Iteration {self.iteration_count} failed: {e}")
                continue
        
        raise Exception("Research failed to complete within max iterations")

    def _execute_phase(self, phase: ResearchPhase, context: Dict) -> Dict:
        messages = [
            {"role": "user", "content": f"Research task: {context.get('original_query', 'Unknown')}\n\nContext: {json.dumps(context, indent=2)}"}
        ]
        
        system_prompt = self.generate_system_prompt(phase, context)
        
        response = self.llm.complete(messages, system_prompt=system_prompt, temperature=0.7)
        
        try:
            result = json.loads(response)
            logger.info(f"Phase {phase.value} completed successfully")
            return result
        except json.JSONDecodeError:
            logger.warning(f"Phase {phase.value} response not valid JSON, attempting extraction")
            return self._extract_json_from_response(response)

    def _extract_json_from_response(self, response: str) -> Dict:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"raw_response": response}

    def _extract_sources(self, context: Dict) -> List[Dict[str, str]]:
        sources = []
        search_results = context.get("search_results", [])
        
        for search_batch in search_results:
            for result in search_batch.get("results", []):
                if result.get("url") and result.get("url") not in [s.get("url") for s in sources]:
                    sources.append({
                        "title": result.get("title", "Unknown"),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", "")[:200]
                    })
        
        return sources[:20]

    def _is_suitable_for_chart(self, content: str) -> Tuple[bool, str]:
        content_lower = content.lower()
        
        chart_indicators = [
            (r'\b(steps?|phases?|stages?)\b', 'flowchart'),
            (r'\b(causes?|factors?|reasons?|contributing)\b', 'mindmap'),
            (r'\b(compared to?|versus|vs\.?|differences?)\b', 'comparison'),
            (r'\b(timeline|history|chronological|evolution)\b', 'timeline'),
            (r'\b(hierarchy|org(anization)?al|structure|levels?)\b', 'graph'),
            (r'\b(process|workflow|pipeline)\b', 'flowchart'),
            (r'\b(components?|parts?|elements?)\b', 'mindmap'),
            (r'\b(growth|trend|increase|decrease|change)\b', 'xychart'),
            (r'\b(relationship|connection|link|association)\b', 'graph'),
            (r'\b(categories?|types?|kinds?|classification)\b', 'pie'),
        ]
        
        for pattern, chart_type in chart_indicators:
            if re.search(pattern, content_lower):
                return True, chart_type
        
        if len(content.split('.')) > 3:
            sentences = content.split('.')
            has_sequence = any(re.search(r'\b(first|second|then|next|finally|after|before)\b', s.lower()) 
                             for s in sentences[:10])
            if has_sequence:
                return True, 'flowchart'
        
        has_numbers = len(re.findall(r'\b\d+\b', content)) >= 3
        if has_numbers and any(kw in content_lower for kw in ['percent', 'percentage', '%', 'ratio', 'proportion']):
            return True, 'pie'
        
        return False, ''

    def _generate_mermaid_chart(self, section: Dict[str, str], chart_type: str) -> Optional[MermaidChart]:
        content = section.get('content', '')
        heading = section.get('heading', 'Chart')
        
        prompt = f"""Generate a Mermaid chart based on the following content. The content is suitable for a {chart_type} chart.

Section Heading: {heading}
Section Content: {content}

Requirements:
1. Output ONLY a valid Mermaid diagram code
2. Choose the best Mermaid chart type based on the content
3. Include the diagram in a code block with ```mermaid
4. Keep the diagram simple and readable
5. Use appropriate Mermaid syntax

Chart types available:
- flowchart TD/LR - for processes and workflows
- graph TD/LR - for relationships and connections
- mindmap - for hierarchies and categories
- timeline - for chronological events
- pie - for percentages and proportions
- xychart - for data trends

Output a JSON object with:
- "chart_type": the mermaid chart type you chose
- "title": a short descriptive title for the chart
- "description": brief explanation of what the chart shows
- "code": the mermaid code block (without the ```mermaid wrapper)
"""

        try:
            response = self.llm.complete(
                [{"role": "user", "content": prompt}],
                system_prompt="You are a data visualization expert. Generate clear, accurate Mermaid diagrams from research content.",
                temperature=0.5,
                max_tokens=2000
            )
            
            result = self._extract_json_from_response(response)
            code = result.get('code', '')
            if code and not code.startswith('```'):
                code = f"```mermaid\n{code}\n```"
            
            return MermaidChart(
                title=result.get('title', heading),
                chart_type=result.get('chart_type', chart_type),
                code=code,
                description=result.get('description', '')
            )
        except Exception as e:
            logger.error(f"Failed to generate chart for '{heading}': {e}")
            return None

    def _generate_charts_for_report(self, sections: List[Dict[str, str]]) -> List[MermaidChart]:
        charts = []
        
        for section in sections:
            is_suitable, chart_type = self._is_suitable_for_chart(section.get('content', ''))
            if is_suitable:
                chart = self._generate_mermaid_chart(section, chart_type)
                if chart and chart.code:
                    charts.append(chart)
                    logger.info(f"Generated {chart.chart_type} chart for: {section.get('heading', 'Unknown')}")
        
        return charts

    def save_report_to_markdown(self, report: ResearchReport, filepath: str = None) -> str:
        if not filepath:
            safe_title = re.sub(r'[^\w\s-]', '', report.title)
            safe_title = re.sub(r'\s+', '_', safe_title).strip('_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"research_report_{safe_title}_{timestamp}.md"
        
        markdown_content = f"""# {report.title}

**Generated:** {report.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Query:** {report.query}  
**Confidence Score:** {report.confidence_score:.0%}  
**Methodology:** {report.methodology}

---

## Executive Summary

{report.executive_summary}

"""

        if report.charts:
            markdown_content += "## Visualizations\n\n"
            for i, chart in enumerate(report.charts, 1):
                markdown_content += f"### {i}. {chart.title}\n\n"
                markdown_content += f"{chart.description}\n\n"
                markdown_content += f"{chart.code}\n\n"

        markdown_content += "## Key Findings\n\n"
        for i, section in enumerate(report.sections, 1):
            markdown_content += f"### {i}. {section.get('heading', 'Section')}\n\n"
            markdown_content += f"{section.get('content', '')}\n\n"
            
            matching_charts = [c for c in report.charts if section.get('heading', '').lower() in c.title.lower()]
            for chart in matching_charts:
                markdown_content += f"\n_{chart.title}:_\n"
                markdown_content += f"{chart.code}\n\n"

        markdown_content += "## Limitations\n\n"
        for limitation in report.limitations:
            markdown_content += f"- {limitation}\n"
        markdown_content += "\n"

        markdown_content += "## Suggested Further Research\n\n"
        for followup in report.suggested_followup:
            markdown_content += f"- {followup}\n"
        markdown_content += "\n"

        markdown_content += "## Sources\n\n"
        for i, source in enumerate(report.sources, 1):
            markdown_content += f"### {i}. {source.get('title', 'Unknown')}\n\n"
            markdown_content += f"- **URL:** {source.get('url', 'N/A')}\n"
            if source.get('snippet'):
                markdown_content += f"- **Snippet:** {source.get('snippet')}\n"
            markdown_content += "\n"

        markdown_content += f"""---

*Report generated by Deep Research Reporting Generator using LM Studio and SearXNG*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Report saved to: {filepath}")
        return filepath

    def interactive_research(self):
        print("\n" + "="*60)
        print("DEEP RESEARCH REPORTING GENERATOR")
        print("="*60)
        print("Enter your research query, or 'quit' to exit.")
        print("Options: --save PATH to save report to markdown")
        print("="*60)
        
        while True:
            user_input = input("\nResearch Query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            save_path = None
            if '--save' in user_input:
                parts = user_input.split('--save')
                query = parts[0].strip()
                save_path = parts[1].strip() if len(parts) > 1 else None
            else:
                query = user_input
            
            print(f"\n{'='*60}")
            print("INITIATING DEEP RESEARCH")
            print(f"Query: {query}")
            if save_path:
                print(f"Save to: {save_path}")
            print("="*60)
            
            try:
                report = self.execute_research(query, save_path=save_path)
                self._display_report(report)
                
                if report.filepath:
                    print(f"\n[SAVED] Report saved to: {report.filepath}")
                
                if report.charts:
                    print(f"\n[CHARTS] Generated {len(report.charts)} Mermaid chart(s)")
                    for i, chart in enumerate(report.charts, 1):
                        print(f"  {i}. {chart.title} ({chart.chart_type})")
                        
            except Exception as e:
                print(f"\nError during research: {e}")

    def research_to_file(self, query: str, filepath: str = None) -> str:
        report = self.execute_research(query, save_path=filepath)
        self._display_report(report)
        return report.filepath

    def _display_report(self, report: ResearchReport):
        print(f"\n{'#'*60}")
        print(report.title.upper())
        print(f"{'#'*60}")
        
        print(f"\n## Executive Summary\n{report.executive_summary}")
        
        print(f"\n## Confidence Score: {report.confidence_score:.0%}")
        
        print("\n## Key Sections:")
        for i, section in enumerate(report.sections, 1):
            print(f"\n### {i}. {section.get('heading', 'Section')}")
            print(section.get('content', '')[:500] + ('...' if len(section.get('content', '')) > 500 else ''))
        
        if report.sources:
            print(f"\n## Sources ({len(report.sources)} total):")
            for i, source in enumerate(report.sources[:10], 1):
                print(f"{i}. {source.get('title', 'Unknown')}")
                print(f"   URL: {source.get('url', 'Unknown')}")
        
        if report.limitations:
            print(f"\n## Limitations")
            for lim in report.limitations:
                print(f"- {lim}")
        
        if report.suggested_followup:
            print(f"\n## Suggested Further Research")
            for follow in report.suggested_followup:
                print(f"- {follow}")


def main(test_mode: bool = False, query: Optional[str] = None, save_path: Optional[str] = None):
    print("Initializing Deep Research Reporting Generator...")
    print("-" * 40)
    
    try:
        llm = LMStudioClient()
        print(f"[OK] LLM Client connected (model: {llm.model})")
    except Exception as e:
        print(f"[FAIL] LLM Client failed: {e}")
        return
    
    try:
        search = SearXNGClient()
        test_results = search.search("test query", num_results=1)
        print(f"[OK] Search Client connected (test: {len(test_results)} results)")
    except Exception as e:
        print(f"[FAIL] Search Client failed: {e}")
        return

    researcher = DeepResearcher(llm, search)
    
    if test_mode:
        print("\n[TEST MODE] Running quick test...")
        test_report = ResearchReport(
            title="Test Report: Capital of France",
            executive_summary="Paris is the capital and largest city of France. It has been the nation's center of administration since the medieval period. This report confirms Paris as the capital based on multiple authoritative sources.",
            sections=[
                {"heading": "Definition of Capital", "content": "A capital city is the primary city or town where a state's government is located. For France, this is Paris. The government institutions including the President (Elysee Palace), Parliament (Palais Bourbon), and Prime Minister (Hotel de Matignon) are all headquartered in Paris."},
                {"heading": "Historical Context", "content": "Paris has been the capital of France since the medieval era. The city became the political center during the reign of Philip II in the 12th century. Other cities like Lyon, Versailles, and Bordeaux have served as administrative centers at different times in history."},
                {"heading": "Government Functions", "content": "Paris serves as the seat of all three branches of the French government: executive (President and Prime Minister), legislative (Parliament), and judicial (Supreme Court). Key institutions include Elysee Palace, Hotel de Matignon, Palais Bourbon, and Conseil Constitutionnel."}
            ],
            sources=[
                {"title": "France - Wikipedia", "url": "https://en.wikipedia.org/wiki/France", "snippet": "Paris is the capital and most populous city of France."},
                {"title": "Government of France - Britannica", "url": "https://www.britannica.com/topic/government-of-France", "snippet": "Paris is the seat of the French government."}
            ],
            methodology="Web search via SearXNG and LLM analysis",
            confidence_score=0.95,
            limitations=["Information limited to publicly available web sources"],
            suggested_followup=["Explore French regional governance structure", "Research Paris's role in EU institutions"],
            charts=[
                MermaidChart(
                    title="French Government Structure",
                    chart_type="graph TD",
                    description="Hierarchy of French government branches",
                    code="```mermaid\ngraph TD\n    A[French Government] --> B[Executive]\n    A --> C[Legislative]\n    A --> D[Judicial]\n    B --> B1[President: Elysee Palace]\n    B --> B2[Prime Minister: Hotel de Matignon]\n    C --> C1[National Assembly]\n    C --> C2[Senate]\n    D --> D1[Supreme Court]\n    D --> D2[Conseil Constitutionnel]\n```"
                )
            ],
            query="What is the capital of France?",
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        researcher._display_report(test_report)
        print("\n[TEST COMPLETE] Deep Research system is operational.")
        return
    
    if query:
        print(f"\n{'='*60}")
        print("DEEP RESEARCH")
        print(f"Query: {query}")
        if save_path:
            print(f"Output: {save_path}")
        print("="*60)
        try:
            report = researcher.execute_research(query, save_path=save_path)
            researcher._display_report(report)
            if report.filepath:
                print(f"\n[SAVED] Report: {report.filepath}")
            if report.charts:
                print(f"[CHARTS] {len(report.charts)} Mermaid chart(s) generated")
        except Exception as e:
            print(f"\nError: {e}")
        return
    
    researcher.interactive_research()


if __name__ == "__main__":
    import sys
    
    test_mode = "--test" in sys.argv
    
    query = None
    save_path = None
    
    args = sys.argv[1:]
    if args:
        if not args[0].startswith('--'):
            query = ' '.join(args)
        else:
            for i, arg in enumerate(args):
                if arg == '--save' and i + 1 < len(args):
                    save_path = args[i + 1]
                elif arg == '--query' and i + 1 < len(args):
                    query = args[i + 1]
    
    main(test_mode=test_mode, query=query, save_path=save_path)
