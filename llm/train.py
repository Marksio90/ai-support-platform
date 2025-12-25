"""
LoRA Fine-tuning for E-commerce Support AI
Trains a Polish language model with LoRA adapters
"""

import os
import json
import yaml
import torch
from typing import Dict, List, Any, Optional
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)
from trl import SFTTrainer


class SupportModelTrainer:
    """
    Trainer for fine-tuning support AI model with LoRA
    """

    def __init__(self, config_path: str = "model_config.yaml"):
        """
        Initialize trainer with configuration

        Args:
            config_path: Path to model configuration YAML
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.base_model_name = self.config['base_model']['name']
        self.output_dir = self.config['training']['output_dir']

        # Initialize tokenizer
        print(f"Loading tokenizer: {self.base_model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)

        # Add padding token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def load_model(self):
        """
        Load base model with quantization
        """
        print(f"Loading base model: {self.base_model_name}")

        # Quantization config
        if self.config['quantization']['enabled']:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=self.config['quantization']['bits'] == 4,
                load_in_8bit=self.config['quantization']['bits'] == 8,
                bnb_4bit_quant_type=self.config['quantization']['type'],
                bnb_4bit_compute_dtype=getattr(
                    torch,
                    self.config['quantization']['compute_dtype']
                ),
                bnb_4bit_use_double_quant=self.config['quantization']['double_quant']
            )
        else:
            bnb_config = None

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Prepare for LoRA training
        model = prepare_model_for_kbit_training(model)

        return model

    def get_lora_config(self) -> LoraConfig:
        """
        Create LoRA configuration
        """
        lora_cfg = self.config['lora']

        return LoraConfig(
            r=lora_cfg['r'],
            lora_alpha=lora_cfg['lora_alpha'],
            target_modules=lora_cfg['target_modules'],
            lora_dropout=lora_cfg['lora_dropout'],
            bias=lora_cfg['bias'],
            task_type=lora_cfg['task_type']
        )

    def prepare_dataset(self, data_path: str = "../data/synthetic/support_dialogs.json") -> Dataset:
        """
        Prepare training dataset from support dialogs

        Args:
            data_path: Path to dialogs JSON

        Returns:
            Hugging Face Dataset
        """
        print(f"Loading training data from {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert dialogs to training format
        training_examples = []

        for dialog in data['dialogs']:
            # Mock context (in real scenario, retrieve from RAG)
            context = f"[Kategoria: {dialog['category']}]"

            # Format prompt
            prompt = self.config['prompt_template'].format(
                system_prompt=self.config['system_prompt'],
                context=context,
                query=dialog['customer_query']
            )

            # Add response
            text = f"{prompt}\n{dialog['ai_response']}</s>"

            training_examples.append({
                "text": text,
                "category": dialog['category']
            })

        print(f"Prepared {len(training_examples)} training examples")

        return Dataset.from_list(training_examples)

    def train(self, dataset: Dataset):
        """
        Fine-tune model with LoRA

        Args:
            dataset: Training dataset
        """
        # Load model
        model = self.load_model()

        # Apply LoRA
        lora_config = self.get_lora_config()
        model = get_peft_model(model, lora_config)

        print("Model with LoRA:")
        model.print_trainable_parameters()

        # Training arguments
        training_cfg = self.config['training']
        training_args = TrainingArguments(
            output_dir=training_cfg['output_dir'],
            num_train_epochs=training_cfg['num_train_epochs'],
            per_device_train_batch_size=training_cfg['per_device_train_batch_size'],
            gradient_accumulation_steps=training_cfg['gradient_accumulation_steps'],
            learning_rate=training_cfg['learning_rate'],
            warmup_steps=training_cfg['warmup_steps'],
            logging_steps=training_cfg['logging_steps'],
            save_steps=training_cfg['save_steps'],
            eval_steps=training_cfg['eval_steps'],
            optim=training_cfg['optim'],
            fp16=training_cfg['fp16'],
            bf16=training_cfg['bf16'],
            save_total_limit=3,
            load_best_model_at_end=True,
            report_to="none"  # Change to "wandb" for experiment tracking
        )

        # Trainer
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            args=training_args,
            tokenizer=self.tokenizer,
            dataset_text_field="text",
            max_seq_length=training_cfg['max_seq_length'],
        )

        # Train
        print("\nStarting training...")
        trainer.train()

        # Save model
        print(f"\nSaving model to {self.output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)

        print("Training complete!")

    def merge_and_save(self, output_path: str = "./models/ecommerce-support-merged"):
        """
        Merge LoRA weights with base model for inference

        Args:
            output_path: Path to save merged model
        """
        print(f"Merging LoRA weights with base model...")

        # Load base model
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            device_map="auto",
            torch_dtype=torch.float16
        )

        # Load LoRA adapter
        model = PeftModel.from_pretrained(model, self.output_dir)

        # Merge
        model = model.merge_and_unload()

        # Save
        print(f"Saving merged model to {output_path}")
        model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        print("Merge complete!")


def main():
    """
    Main training script
    """
    # Initialize trainer
    trainer = SupportModelTrainer("model_config.yaml")

    # Prepare dataset
    dataset = trainer.prepare_dataset()

    # Train
    trainer.train(dataset)

    # Optionally merge for deployment
    # trainer.merge_and_save()


if __name__ == "__main__":
    main()
