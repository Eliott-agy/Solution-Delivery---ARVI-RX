"""MedGemma PEFT/QLoRA stub.

Use this only after prompt baseline and evaluation are stable. Check model access,
license, GPU requirements and official Google/Hugging Face examples before running.
"""

# Recommended flow:
# 1. Convert a small validated dataset into image + instruction + JSON answer examples.
# 2. Use PEFT/QLoRA for adapter training, not full fine-tuning at first.
# 3. Evaluate on held-out final cases.
# 4. Keep non-clinical warning and uncertainty rules.


def main() -> None:
    print("Skeleton only. Connect official MedGemma fine-tuning recipe after validation.")


if __name__ == "__main__":
    main()
