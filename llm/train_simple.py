"""
Simplified LoRA Fine-tuning Script
Ready-to-use training for e-commerce support AI
"""

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)


class SupportAITrainer:
    """Simplified trainer for support AI"""

    def __init__(
        self,
        base_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
        output_dir: str = "./models/ecommerce-support-lora",
        use_4bit: bool = True
    ):
        self.base_model = base_model
        self.output_dir = output_dir
        self.use_4bit = use_4bit

        print(f"Initializing trainer for {base_model}")

    def load_training_data(self, data_path: str = "../data/synthetic/support_dialogs.json"):
        """Load and format training data"""
        print(f"Loading training data from {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Format dialogs for training
        formatted_data = []
        for dialog in data['dialogs']:
            prompt = self._format_prompt(
                query=dialog['customer_query'],
                category=dialog.get('category', '')
            )
            completion = dialog['ai_response']

            formatted_data.append({
                "text": f"{prompt}\n\n{completion}</s>"
            })

        dataset = Dataset.from_list(formatted_data)
        print(f"Loaded {len(dataset)} training examples")

        return dataset

    def _format_prompt(self, query: str, category: str = ""):
        """Format prompt for training"""
        system_prompt = """Jesteś pomocnym asystentem obsługi klienta w polskim sklepie internetowym.
Odpowiadaj uprzejmie, profesjonalnie i konkretnie."""

        return f"""<s>[INST] {system_prompt}

Pytanie klienta: {query}
Kategoria: {category}

Odpowiedz na pytanie klienta. [/INST]"""

    def setup_model_and_tokenizer(self):
        """Setup model with LoRA and tokenizer"""
        print("Loading base model and tokenizer...")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        # Quantization config for 4-bit training
        if self.use_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        else:
            bnb_config = None

        # Load base model
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Prepare for training
        if self.use_4bit:
            model = prepare_model_for_kbit_training(model)

        # LoRA configuration
        lora_config = LoraConfig(
            r=16,  # LoRA rank
            lora_alpha=32,  # LoRA alpha
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Mistral attention modules
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )

        # Get PEFT model
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        return model, tokenizer

    def train(
        self,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        max_length: int = 512
    ):
        """Run training"""

        print("\n" + "="*60)
        print("Starting LoRA Fine-tuning")
        print("="*60 + "\n")

        # Load data
        dataset = self.load_training_data()

        # Setup model
        model, tokenizer = self.setup_model_and_tokenizer()

        # Tokenize dataset
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length"
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            fp16=True,
            save_steps=100,
            logging_steps=10,
            save_total_limit=2,
            report_to="none",
            optim="paged_adamw_8bit" if self.use_4bit else "adamw_torch",
            warmup_steps=50,
            lr_scheduler_type="cosine"
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )

        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator
        )

        # Train
        print("\nStarting training...")
        trainer.train()

        # Save final model
        print(f"\nSaving model to {self.output_dir}")
        trainer.save_model()
        tokenizer.save_pretrained(self.output_dir)

        print("\n" + "="*60)
        print("Training completed!")
        print(f"Model saved to: {self.output_dir}")
        print("="*60 + "\n")


def main():
    """Main training function"""

    print("\n╔" + "="*58 + "╗")
    print("║" + " "*15 + "Support AI - LoRA Training" + " "*17 + "║")
    print("╚" + "="*58 + "╝\n")

    # Check for GPU
    if not torch.cuda.is_available():
        print("⚠️  WARNING: No GPU detected!")
        print("Training will be VERY slow on CPU.")
        print("Recommend using GPU with at least 8GB VRAM.\n")

        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            return

    # Initialize trainer
    trainer = SupportAITrainer(
        base_model="mistralai/Mistral-7B-Instruct-v0.2",
        output_dir="./models/ecommerce-support-lora",
        use_4bit=True  # Use 4-bit for efficient training
    )

    # Run training
    trainer.train(
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4
    )

    print("\n✅ Training complete!")
    print("\nNext steps:")
    print("1. Test the model: python inference.py")
    print("2. Update llm/service.py to use the fine-tuned model")
    print("3. Rebuild Docker images with new model")


if __name__ == "__main__":
    main()
