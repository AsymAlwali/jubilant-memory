from memoryos.core import MemoryOS

print("\n🧠 JUBILANT MEMORY v0.1")
print("Intelligence Remembers")
print("=" * 45)

memory = MemoryOS()

facts = [
    "Asym is building One Question, an AI knowledge platform.",
    "Asym uses GitHub Codespaces for development.",
    "AwesomeAI will use MemoryOS for persistent memory.",
    "Asym is researching how language models process tokens."
]

print("\n📥 STORING MEMORIES")

ids = []

for fact in facts:
    memory_id = memory.remember(fact)
    ids.append(memory_id)
    print("Stored:", fact)

print("\n🔍 SEMANTIC RECALL")

results = memory.recall(
    "Where does Asym write his code?",
    limit=2
)

for result in results:
    print(
        f"[{result['score']:.3f}]",
        result["content"]
    )

print("\n✏️ UPDATING MEMORY")

updated = memory.update(
    ids[1],
    "Asym develops projects using GitHub Codespaces and Termux."
)

print("Update successful:", updated)

print("\n🗑️ DELETING MEMORY")

deleted = memory.forget(ids[3])

print("Deletion successful:", deleted)

memory.close()

print("\n🔄 TESTING PERSISTENCE")

memory = MemoryOS()

results = memory.recall(
    "What tools does Asym use for development?",
    limit=2
)

for result in results:
    print(
        f"[{result['score']:.3f}]",
        result["content"]
    )

memory.close()

print("\n✅ EXPERIMENT COMPLETE")
