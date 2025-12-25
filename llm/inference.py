"""
LLM Inference Server for E-commerce Support AI
Handles generation with LoRA model + RAG
"""

import os
import sys
import yaml
import torch
from typing import Dict, List, Any, Optional
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)
from peft import PeftModel

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rag.retriever import RAGRetriever


class SupportAI:
    """
    Main AI inference engine combining LLM + RAG
    """

    def __init__(
        self,
        model_path: str = "./models/ecommerce-support-lora",
        base_model: Optional[str] = None,
        config_path: str = "model_config.yaml",
        use_rag: bool = True
    ):
        """
        Initialize AI inference

        Args:
            model_path: Path to fine-tuned model or LoRA adapter
            base_model: Base model name (if using LoRA adapter)
            config_path: Path to model config
            use_rag: Whether to use RAG for retrieval
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.use_rag = use_rag

        # Initialize RAG
        if self.use_rag:
            print("Initializing RAG retriever...")
            self.retriever = RAGRetriever()
            if not os.path.exists(self.retriever.index_path):
                print("Building RAG index...")
                self.retriever.build_index()
        else:
            self.retriever = None

        # Load model and tokenizer
        print(f"Loading model from {model_path}")
        self.load_model(model_path, base_model)

        # Generation config
        self.gen_config = self.config['generation']
        self.guardrails = self.config['guardrails']

    def load_model(self, model_path: str, base_model: Optional[str] = None):
        """
        Load model and tokenizer
        """
        # Check if it's a LoRA adapter or full model
        is_lora = os.path.exists(os.path.join(model_path, "adapter_config.json"))

        if is_lora:
            # Load base model + LoRA adapter
            if base_model is None:
                base_model = self.config['base_model']['name']

            print(f"Loading base model: {base_model}")

            # Quantization for efficient inference
            if self.config['quantization']['enabled']:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=self.config['quantization']['bits'] == 4,
                    load_in_8bit=self.config['quantization']['bits'] == 8,
                    bnb_4bit_quant_type=self.config['quantization']['type'],
                    bnb_4bit_compute_dtype=getattr(
                        torch,
                        self.config['quantization']['compute_dtype']
                    )
                )
            else:
                bnb_config = None

            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            # Load LoRA adapter
            print(f"Loading LoRA adapter from {model_path}")
            model = PeftModel.from_pretrained(model, model_path)

            tokenizer = AutoTokenizer.from_pretrained(model_path)
        else:
            # Load full fine-tuned model
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                torch_dtype=torch.float16
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Add padding token if missing
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        self.model = model
        self.tokenizer = tokenizer

        print("Model loaded successfully")

    def generate(
        self,
        query: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response for query

        Args:
            query: User query
            context: Optional pre-retrieved context
            **kwargs: Additional generation parameters

        Returns:
            Response dictionary with answer, confidence, sources
        """
        # Retrieve context from RAG if not provided
        if context is None and self.use_rag:
            rag_results = self.retriever.retrieve(query, top_k=5)
            context = self.retriever.format_context(rag_results)
            sources = self.retriever.get_sources(rag_results)
        else:
            context = context or ""
            sources = []

        # Format prompt
        prompt = self.config['prompt_template'].format(
            system_prompt=self.config['system_prompt'],
            context=context,
            query=query
        )

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config['training']['max_seq_length']
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Generate
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_new_tokens", self.gen_config['max_new_tokens']),
            "temperature": kwargs.get("temperature", self.gen_config['temperature']),
            "top_p": kwargs.get("top_p", self.gen_config['top_p']),
            "top_k": kwargs.get("top_k", self.gen_config['top_k']),
            "repetition_penalty": kwargs.get("repetition_penalty", self.gen_config['repetition_penalty']),
            "do_sample": kwargs.get("do_sample", self.gen_config['do_sample']),
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "return_dict_in_generate": True,
            "output_scores": True
        }

        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        # Decode response
        response_ids = outputs.sequences[0][inputs['input_ids'].shape[1]:]
        response = self.tokenizer.decode(response_ids, skip_special_tokens=True)

        # Calculate confidence (simplified - use logits in production)
        # For demo, estimate based on context similarity
        confidence = self._estimate_confidence(query, context, response)

        # Check guardrails
        requires_human = confidence < self.guardrails['confidence_threshold']

        return {
            "answer": response.strip(),
            "confidence": confidence,
            "sources": sources,
            "requires_human": requires_human,
            "context_used": context
        }

    def _estimate_confidence(
        self,
        query: str,
        context: str,
        response: str
    ) -> float:
        """
        Estimate confidence score

        In production, this should use:
        - Token probabilities from generation
        - Semantic similarity between query and context
        - Response coherence metrics

        For demo, simplified heuristic.
        """
        # Simple heuristic: based on context length and response length
        confidence = 0.8  # Default

        if not context or len(context) < 100:
            confidence -= 0.2

        if len(response) < 50:
            confidence -= 0.1

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "nie jestem pewien",
            "nie wiem",
            "skontaktuj się",
            "przekażę",
            "nie mogę odpowiedzieć"
        ]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))


def main():
    """
    Test inference
    """
    # Note: For testing without trained model, use base model directly
    ai = SupportAI(
        model_path="mistralai/Mistral-7B-Instruct-v0.2",  # Use base model for demo
        use_rag=True
    )

    # Test queries
    test_queries = [
        "Jak mogę zwrócić produkt?",
        "Jakie są koszty dostawy?",
        "Chcę zmienić adres dostawy"
    ]

    print("\n" + "="*80)
    print("Testing Support AI Inference")
    print("="*80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        result = ai.generate(query)

        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Requires Human: {result['requires_human']}")
        print(f"Sources: {result['sources']}")


if __name__ == "__main__":
    main()
