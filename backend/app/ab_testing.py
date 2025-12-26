"""
A/B Testing Framework for AI Services
Allows testing different LLM/RAG configurations and comparing performance
"""

import hashlib
import os
from typing import Dict, Any, Optional, Literal
from datetime import datetime
import json


class ABTest:
    """A/B testing controller for AI services"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize A/B testing

        Args:
            config_path: Path to A/B test configuration file
        """
        self.config_path = config_path or os.getenv(
            "AB_TEST_CONFIG",
            "/app/ab_test_config.json"
        )
        self.config = self._load_config()
        self.results: Dict[str, list] = {"A": [], "B": []}

    def _load_config(self) -> Dict[str, Any]:
        """Load A/B test configuration"""
        default_config = {
            "enabled": os.getenv("AB_TEST_ENABLED", "false").lower() == "true",
            "split_ratio": 0.5,  # 50/50 split
            "variant_a": {
                "name": "rule-based",
                "llm_service_url": "http://llm-service:8001",
                "rag_service_url": "http://rag-service:8002"
            },
            "variant_b": {
                "name": "openai",
                "llm_service_url": "http://llm-service-openai:8001",
                "rag_service_url": "http://rag-service:8002"
            }
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Warning: Could not load A/B config: {e}")

        return default_config

    def assign_variant(
        self,
        user_id: Optional[str] = None,
        query_id: Optional[str] = None
    ) -> Literal["A", "B"]:
        """
        Assign user to variant A or B

        Uses consistent hashing to ensure same user always gets same variant

        Args:
            user_id: User identifier (optional)
            query_id: Query identifier as fallback

        Returns:
            "A" or "B" variant
        """
        if not self.config["enabled"]:
            return "A"  # Default to variant A if testing disabled

        # Use user_id for consistency, fallback to query_id
        identifier = user_id or query_id or str(datetime.utcnow().timestamp())

        # Hash the identifier
        hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)

        # Determine variant based on split ratio
        split_ratio = self.config["split_ratio"]
        threshold = hash_value / (2**128)  # Normalize to 0-1

        return "A" if threshold < split_ratio else "B"

    def get_variant_config(self, variant: Literal["A", "B"]) -> Dict[str, str]:
        """
        Get configuration for specific variant

        Args:
            variant: "A" or "B"

        Returns:
            Variant configuration with service URLs
        """
        variant_key = "variant_a" if variant == "A" else "variant_b"
        return self.config[variant_key]

    def record_result(
        self,
        variant: Literal["A", "B"],
        query: str,
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record A/B test result for analysis

        Args:
            variant: Which variant was used
            query: User query
            response: AI response
            metadata: Additional metadata (user_id, timestamp, etc.)
        """
        result = {
            "variant": variant,
            "query": query,
            "response": response,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        self.results[variant].append(result)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get A/B testing statistics

        Returns:
            Statistics for both variants
        """
        stats = {
            "enabled": self.config["enabled"],
            "variant_a": self._calculate_variant_stats("A"),
            "variant_b": self._calculate_variant_stats("B")
        }

        return stats

    def _calculate_variant_stats(self, variant: Literal["A", "B"]) -> Dict[str, Any]:
        """Calculate statistics for a variant"""
        results = self.results[variant]

        if not results:
            return {
                "name": self.config[f"variant_{variant.lower()}"]["name"],
                "total_queries": 0,
                "avg_confidence": 0.0,
                "automation_rate": 0.0,
                "avg_response_length": 0
            }

        total = len(results)
        confidences = [r["response"].get("confidence", 0) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        automated = sum(
            1 for r in results
            if not r["response"].get("requires_human", True)
        )
        automation_rate = (automated / total * 100) if total > 0 else 0

        response_lengths = [
            len(r["response"].get("answer", ""))
            for r in results
        ]
        avg_response_length = (
            sum(response_lengths) / len(response_lengths)
            if response_lengths else 0
        )

        return {
            "name": self.config[f"variant_{variant.lower()}"]["name"],
            "total_queries": total,
            "avg_confidence": round(avg_confidence, 3),
            "automation_rate": round(automation_rate, 1),
            "avg_response_length": round(avg_response_length, 0),
            "automated_queries": automated,
            "human_required": total - automated
        }

    def export_results(self, filepath: str):
        """Export A/B test results to JSON file"""
        data = {
            "config": self.config,
            "stats": self.get_stats(),
            "results": self.results,
            "exported_at": datetime.utcnow().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath


# Global A/B testing instance
ab_test = ABTest()
