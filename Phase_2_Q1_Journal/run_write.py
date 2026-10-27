import sys

md = open("mentor_feedback_content.md", encoding="utf-8").read()
with open(r"d:\KLTN\cir-faiss-thesis\Phase_2_Q1_Journal\mentor_feedback.md", "w", encoding="utf-8") as f:
    f.write(md)
print("Written", len(md), "chars")
