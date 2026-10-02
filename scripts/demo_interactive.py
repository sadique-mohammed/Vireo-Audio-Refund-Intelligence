import sys
import os
from pathlib import Path

# Add the project root to sys.path so we can import src
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.vireo import reasons
from src.vireo import config as C

def main():
    print("===========================================")
    print(" Vireo Refund Intelligence - Live AI Demo  ")
    print("===========================================")
    print(f"Model: {C.GROQ_MODEL}")
    print(f"Prompt Version: {C.PROMPT_VERSION}")
    print("-------------------------------------------\n")
    print("Type 'quit' or 'exit' in the customer message to stop.\n")

    while True:
        try:
            print("Enter Customer Message:")
            customer_message = input("> ").strip()
            
            if customer_message.lower() in ('quit', 'exit', 'q'):
                break
                
            print("\nEnter Agent Notes:")
            agent_notes = input("> ").strip()
            
            if not customer_message and not agent_notes:
                print("No input provided. Skipping...\n")
                continue

            print(f"\n[... Requesting {C.GROQ_MODEL} ...]")
            
            # Load prompt
            version, template, prompt_hash = reasons.load_prompt()
            
            # Scrub PII
            scrubbed_message = reasons.scrub(customer_message)
            scrubbed_notes = reasons.scrub(agent_notes, notes=True)
            
            # Render prompt
            prompt = reasons.render(template, code="UNKNOWN", message=scrubbed_message, notes=scrubbed_notes)
            
            # Fetch AI response
            reasons.require_groq_key()
            response_text, usage = reasons.call_with_backoff(reasons.groq_provider, prompt)
            
            parsed = reasons.parse_output(response_text)
            
            print("\n================ RESULT =================")
            print(f"Raw Model Output:\n{response_text}\n")
            if parsed:
                verified = reasons.evidence_verified(parsed.evidence, scrubbed_message, scrubbed_notes, parsed.reason)
                print("Parsed Classification:")
                print(f"  Reason:           {parsed.reason}")
                print(f"  Replacement Sent: {parsed.replacement_sent}")
                print(f"  Certainty:        {parsed.certainty}")
                print(f"  Evidence:         \"{parsed.evidence}\"")
                print(f"  Evidence Valid:   {'Yes' if verified else 'No (Hallucinated!)'}")
            else:
                print("ERROR: AI output did not match required JSON schema.")
                
            print("=========================================\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            break

if __name__ == "__main__":
    main()
