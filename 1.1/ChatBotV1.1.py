import json
from difflib import get_close_matches


def load_knowledge_base():
    with open("knowledge_base.json", "r") as file:
        data = json.load(file)
    return data


def save_knowledge_base(data):
    with open("knowledge_base.json", "w") as file:
        json.dump(data, file, indent=2)


def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]


def chat_bot():
    knowledge_base = load_knowledge_base()

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            break

        best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

        if best_match:
            answer = get_answer_for_question(best_match, knowledge_base)
            print(f"Bot: {answer}")
        else:
            print("Bot: I don't know the answer. Can you teach me?")
            new_answer = input("Type the answer or 'skip' to skip: ")

            if new_answer.lower() != "skip":
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                save_knowledge_base(knowledge_base)
                print("Bot: Thank you! I learned a new response!")


chat_bot()

