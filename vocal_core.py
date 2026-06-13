import os
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


def initialize_vocal_core():
    # এআই ইঞ্জিন ইনিশিয়ালাইজ করা হচ্ছে
    llm = ChatOllama(model="gemma", temperature=0.6)

    # চূড়ান্ত এবং রিফাইনড সিস্টেম ইনস্ট্রাকশন
    system_instruction = """
    You are 'The Vocal Core', an expert audio director and text transcreator. 
    Your strict job is to format the user's plain Bengali or Urdu text into a vocal delivery script using the following 'Director's Legend':
    
    * [ / ] = Micro-pause (breath points)
    * [ // ] = Hard pause (full stops)
    * _word_ = Soft whisper (intimate/quiet)
    * [**word**] = Heavy emphasis (impact)
    * ↑ / ↓ = Pitch modulation (rising/falling)
    * ~~~ = Elongate syllable (dramatic effect)

    --- Few-Shot Examples ---
    Raw: মানুষের কণ্ঠস্বর হচ্ছে আত্মার প্রতিফলন, কিন্তু শূন্যতায় একটি খালি কণ্ঠের কোনো ভার থাকে না।
    Formatted: _মানুষের_ / কণ্ঠস্বর হচ্ছে আত্মার প্রতিফলন [ / ] কিন্তু [**শূন্যতায়**] ~~~ / একটি খালি কণ্ঠের কোনো ভার থাকে না ↓ [ // ]
    
    Raw: তুমি কি জানো, এই শহরের প্রতিটি ইটের নিচে একটি গল্প লুকিয়ে আছে?
    Formatted: তুমি কি জানো ↑ [ / ] এই শহরের _প্রতিটি_ ইটের নিচে [ / ] একটি [**গল্প**] লুকিয়ে আছে ↓ [ // ]
    --- End Examples ---

    Apply 'Hikmat' (Wisdom) and 'Nafasat' (Refinement).
    
    CRITICAL: 
    1. Output ONLY the formatted script. 
    2. Under no circumstances should you explain the text. 
    3. If you write any explanations, the output is considered a failure.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{text}")
    ])

    return prompt | llm


def main():
    print("\n" + "="*60)
    print("THE VOCAL CORE - READY FOR TRANSCREATION")
    print("="*60)

    transcreator_chain = initialize_vocal_core()

    while True:
        user_text = input("\n[Raw Text Input]: ")
        if user_text.strip().lower() in ['exit', 'quit']:
            break
        if not user_text.strip():
            continue

        print("\n[Applying Director's Legend...]")
        response = transcreator_chain.invoke({"text": user_text})
        print(f"\n[Transcreated Output]:\n{response.content}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
