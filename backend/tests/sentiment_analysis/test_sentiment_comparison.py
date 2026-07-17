"""Quick comparison test: Transformer (hybrid) vs Lexikon sentiment analysis."""
from models.sentiment_analyzer import SentimentAnalyzer

tests = [
    ('Die Arbeit hier ist fantastisch und das Team ist sehr unterstützend!', 'positive'),
    ('Katastrophales Management und keine Work-Life-Balance.', 'negative'),
    ('Es ist okay, nichts Besonderes.', 'neutral'),
    ('Die interessanten Projekte und das Maß an projektinternen Gestaltungsmöglichkeiten.', 'positive'),
    ('Viel zu viel Stress und keine Wertschätzung der Mitarbeiter.', 'negative'),
    ('Der Zusammenhalt ist gut. Bezahlung ist top. Das macht einen Jobwechsel so schwer.', 'positive'),
    ('Leider ist die Bezahlung schlecht und die Arbeitszeiten sind unfair.', 'negative'),
    ('Nicht schlecht, aber auch nicht besonders gut.', 'neutral'),
]

# --- Transformer Hybrid (Default) ---
print("=== Transformer Hybrid Tests (Default) ===")
sa_t = SentimentAnalyzer()
print(f"Mode: {sa_t.mode}")
print()

correct_t = 0
for text, expected in tests:
    r = sa_t.analyze_sentiment(text)
    ok = r['sentiment'] == expected
    if ok:
        correct_t += 1
    icon = '\u2705' if ok else '\u274C'
    print(f"  {icon} [{expected:>8}] -> {r['sentiment']:>8}  (pol={r['polarity']:+.2f}, conf={r['confidence']:.2f}) | {text[:60]}")

print(f"\nTransformer Hybrid Accuracy: {correct_t}/{len(tests)} ({correct_t/len(tests)*100:.0f}%)")

# --- Lexikon (Reserve) ---
print("\n=== Lexikon Tests (Reserve) ===")
sa_l = SentimentAnalyzer(mode='lexicon')

correct_l = 0
for text, expected in tests:
    r = sa_l.analyze_sentiment(text)
    ok = r['sentiment'] == expected
    if ok:
        correct_l += 1
    icon = '\u2705' if ok else '\u274C'
    print(f"  {icon} [{expected:>8}] -> {r['sentiment']:>8}  (pol={r['polarity']:+.2f}, conf={r['confidence']:.2f}) | {text[:60]}")

print(f"\nLexikon Accuracy: {correct_l}/{len(tests)} ({correct_l/len(tests)*100:.0f}%)")

# --- Vergleich ---
print("\n=== Vergleich ===")
print(f"Transformer Hybrid: {correct_t}/{len(tests)} ({correct_t/len(tests)*100:.0f}%)")
print(f"Lexikon:            {correct_l}/{len(tests)} ({correct_l/len(tests)*100:.0f}%)")
diff = correct_t - correct_l
if diff > 0:
    print(f"-> Transformer Hybrid ist {diff} Treffer besser (+{diff/len(tests)*100:.0f}%)")
elif diff < 0:
    print(f"-> Lexikon ist {-diff} Treffer besser (+{-diff/len(tests)*100:.0f}%)")
else:
    print("-> Gleiche Accuracy")
