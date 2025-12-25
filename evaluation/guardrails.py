"""
Guardrails and safety checks for Support AI
Ensures responses are safe, accurate, and compliant
"""

from typing import Dict, Any, List, Optional
import re


class Guardrails:
    """
    Safety and quality guardrails for AI responses
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize guardrails

        Args:
            config: Guardrails configuration
        """
        self.config = config or self._default_config()

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Default guardrails configuration"""
        return {
            "confidence_threshold": 0.7,
            "max_response_length": 500,
            "min_response_length": 20,
            "forbidden_topics": [
                "medical", "legal", "financial_advice"
            ],
            "forbidden_actions": [
                "refund_without_verification",
                "share_personal_data",
                "make_promises"
            ],
            "required_citations": True
        }

    def check_response(
        self,
        query: str,
        response: str,
        confidence: float,
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Check response against guardrails

        Args:
            query: User query
            response: AI response
            confidence: Confidence score
            sources: Source documents used

        Returns:
            Check results with pass/fail and reasons
        """
        checks = {
            "passed": True,
            "requires_human": False,
            "warnings": [],
            "errors": []
        }

        # 1. Confidence threshold
        if confidence < self.config["confidence_threshold"]:
            checks["requires_human"] = True
            checks["warnings"].append(
                f"Low confidence ({confidence:.2f} < {self.config['confidence_threshold']})"
            )

        # 2. Response length
        response_len = len(response)
        if response_len > self.config["max_response_length"]:
            checks["warnings"].append(
                f"Response too long ({response_len} > {self.config['max_response_length']})"
            )

        if response_len < self.config["min_response_length"]:
            checks["errors"].append(
                f"Response too short ({response_len} < {self.config['min_response_length']})"
            )
            checks["passed"] = False

        # 3. Forbidden topics
        forbidden = self._check_forbidden_topics(query, response)
        if forbidden:
            checks["requires_human"] = True
            checks["errors"].append(f"Forbidden topic detected: {forbidden}")
            checks["passed"] = False

        # 4. Citations required
        if self.config["required_citations"] and not sources:
            checks["warnings"].append("No sources cited")
            checks["requires_human"] = True

        # 5. Hallucination detection (simple heuristics)
        if self._check_hallucination(response):
            checks["requires_human"] = True
            checks["warnings"].append("Possible hallucination detected")

        # 6. Personal data leakage
        if self._check_personal_data(response):
            checks["errors"].append("Personal data detected in response")
            checks["passed"] = False
            checks["requires_human"] = True

        return checks

    def _check_forbidden_topics(self, query: str, response: str) -> Optional[str]:
        """Check for forbidden topics"""
        text = (query + " " + response).lower()

        forbidden_patterns = {
            "medical": [
                r"diagnoz", r"lek (na|od)", r"chorob", r"schorzeni",
                r"objaw", r"leczeni"
            ],
            "legal": [
                r"prawnik", r"sąd", r"pozew", r"radca prawny",
                r"interpretacja prawna"
            ],
            "financial_advice": [
                r"inwestuj", r"giełda", r"akcje", r"kryptowalut",
                r"jak zarabiać"
            ]
        }

        for topic, patterns in forbidden_patterns.items():
            if topic in self.config["forbidden_topics"]:
                for pattern in patterns:
                    if re.search(pattern, text):
                        return topic

        return None

    def _check_hallucination(self, response: str) -> bool:
        """
        Simple hallucination detection
        In production, use more sophisticated methods
        """
        # Check for overly specific claims without sources
        specific_patterns = [
            r"\d{10,}",  # Very specific numbers (like phone numbers)
            r"dokładnie \d+ (złotych|zł)",  # Specific prices not from context
            r"gwarantuj[eę]",  # Guarantees
        ]

        for pattern in specific_patterns:
            if re.search(pattern, response.lower()):
                return True

        return False

    def _check_personal_data(self, response: str) -> bool:
        """Check for personal data leakage"""
        pii_patterns = [
            r"\d{11}",  # PESEL
            r"\d{2}-\d{3}",  # Postal code
            r"\d{2} \d{4} \d{4} \d{4} \d{4} \d{4}",  # Bank account
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
        ]

        for pattern in pii_patterns:
            if re.search(pattern, response):
                return True

        return False

    def apply_fallback(
        self,
        query: str,
        check_results: Dict[str, Any]
    ) -> str:
        """
        Generate fallback response if checks fail

        Args:
            query: Original query
            check_results: Guardrails check results

        Returns:
            Fallback response
        """
        if check_results["errors"]:
            return (
                "Przepraszam, ale nie mogę odpowiedzieć na to pytanie. "
                "Skontaktuję Cię z naszym zespołem obsługi klienta, "
                "który pomoże Ci w tej sprawie. "
                "\n\nMożesz też napisać na: pomoc@sklep.pl lub zadzwonić: 22 123 45 67"
            )

        if check_results["requires_human"]:
            return (
                "Rozumiem Twoje pytanie, jednak aby udzielić Ci precyzyjnej odpowiedzi, "
                "zalecam kontakt z naszym konsultantem. "
                "\n\n📧 Email: pomoc@sklep.pl\n📞 Telefon: 22 123 45 67 (pn-pt 9-17)"
            )

        return None  # No fallback needed


if __name__ == "__main__":
    # Test guardrails
    guardrails = Guardrails()

    test_cases = [
        {
            "query": "Jak mogę zwrócić produkt?",
            "response": "Aby zwrócić produkt, zaloguj się na konto i przejdź do 'Zwroty'. Masz 14 dni na zwrot zgodnie z regulaminem.",
            "confidence": 0.9,
            "sources": ["Regulamin zwrotów"]
        },
        {
            "query": "Czy ten lek pomoże na ból głowy?",
            "response": "To może być pomocne na ból głowy",
            "confidence": 0.5,
            "sources": []
        },
        {
            "query": "Jakie są koszty dostawy?",
            "response": "Tak",
            "confidence": 0.8,
            "sources": ["FAQ"]
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}")
        print(f"{'='*80}")
        print(f"Query: {case['query']}")
        print(f"Response: {case['response']}")
        print(f"Confidence: {case['confidence']}")

        results = guardrails.check_response(
            case['query'],
            case['response'],
            case['confidence'],
            case['sources']
        )

        print(f"\nResults: {results}")

        if not results['passed'] or results['requires_human']:
            fallback = guardrails.apply_fallback(case['query'], results)
            print(f"\nFallback response:\n{fallback}")
