"""Gemma 4 + Unsloth LoRA stub for the educational project.

This file is intentionally a skeleton. Use it only after baseline, dataset and metrics
are stable. Adapt to the current Unsloth documentation and available GPU.
"""

# Key principles for Gemma 4 multimodal LoRA:
# - Prefer E2B/E4B for multimodal student experiments.
# - Put image content before the text instruction.
# - Start with LoRA, not full fine-tuning.
# - Keep finetune_vision_layers=False at first.
# - Validate JSON, hallucinations, sensitivity and specificity after training.


def main() -> None:
    print("Skeleton only. Read docs/ and connect Unsloth FastVisionModel when resources are available.")


if __name__ == "__main__":
    main()
