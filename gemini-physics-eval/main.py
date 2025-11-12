import os
import pandas as pd
import google.genai as genai

# ==================================================
# 1️⃣ Configure Gemini API key
# ==================================================
client = genai.Client(api_key="AIzaSyBCo7pLmlXXi4F-V6NK6CEkBVqsklnLErk")  # <-- Replace with your real Gemini API key

# ==================================================
# 2️⃣ File paths
# ==================================================
excel_path = "physics_questions.xlsx"   # <-- Your Excel file
image_folder = "images"                 # <-- Folder containing all images

# ==================================================
# 3️⃣ Load Excel file
# ==================================================
df = pd.read_excel(excel_path)

# Ensure required columns exist
required_cols = [
    "Gemini Response",
    "Complexity Level (Task 2)",
    "Refined Prompt/Hint (Task 3)",
    "Gemini Response with Hint (Task 3)",
    "Gemini Response with Search (Task 3)",
    "Gemini Response with Search & Hint (Task 3)"
]
for col in required_cols:
    if col not in df.columns:
        df[col] = ""

# ==================================================
# 4️⃣ Model name
# ==================================================
model = "gemini-2.0-flash"

# Columns that may contain image filenames
image_columns = [
    "Qn reference Image",
    "Options",
    "Options.1",
    "Options.2",
    "Options.3",
    "Options.4"
]

# ==================================================
# 5️⃣ Helper function to prepare contents
# ==================================================
def prepare_contents(row, use_hint=False):
    """Return list of strings and/or uploaded files for Gemini input."""
    question_text = str(row.get("question", ""))
    options_text = str(row.get("options", ""))
    
    contents = [f"Question: {question_text}\nOptions: {options_text}"]
    
    # Include hint if needed
    if use_hint and row.get("Refined Prompt/Hint (Task 3)"):
        contents.append(f"Hint: {row['Refined Prompt/Hint (Task 3)']}")

    # Attach images
    for col in image_columns:
        if col in row and isinstance(row[col], str) and row[col].endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(image_folder, row[col])
            if os.path.exists(img_path):
                try:
                    uploaded_file = client.files.upload(file=img_path)
                    contents.append(uploaded_file)
                except Exception as e:
                    print(f"⚠️ Error uploading {img_path}: {e}")
            else:
                print(f"⚠️ Missing image file: {img_path}")
    return contents

# ==================================================
# 6️⃣ Main processing loop
# ==================================================
for index, row in df.iterrows():
    print(f"\nProcessing {index+1}/{len(df)} → {row.get('pid', 'Unknown ID')}")
    
    question_text = str(row.get("question", ""))  # For Task 2

    # --------------------------
    # Task 1: Gemini Response
    # --------------------------
    contents_task1 = prepare_contents(row)
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents_task1
        )
        answer_text = response.text.strip() if response.text else "(No answer returned)"
    except Exception as e:
        answer_text = f"Error: {e}"
    df.loc[index, "Gemini Response"] = answer_text
    print("✅ Gemini Response:", answer_text[:200], "..." if len(answer_text) > 200 else "")

    # --------------------------
    # Task 2: Complexity Classification
    # --------------------------
    question_text_lower = question_text.lower()
    if any(k in question_text_lower for k in ["ray", "mirror", "lens", "reflection", "refraction", "optical"]):
        complexity = "Medium"
    elif any(k in question_text_lower for k in ["capacitan", "torque", "magnetic", "rotation", "angular", "emf", "current", "photoelectric", "shm"]):
        complexity = "Hard"
    else:
        complexity = "Easy"
    df.loc[index, "Complexity Level (Task 2)"] = complexity
    print(f"✅ Complexity Level: {complexity}")

    # --------------------------
    # Task 3: Responses with Hint
    # --------------------------
    # With Hint
    if row.get("Refined Prompt/Hint (Task 3)"):
        contents_hint = prepare_contents(row, use_hint=True)
        try:
            response_hint = client.models.generate_content(
                model=model,
                contents=contents_hint
            )
            df.loc[index, "Gemini Response with Hint (Task 3)"] = response_hint.text.strip() if response_hint.text else "(No answer returned)"
        except Exception as e:
            df.loc[index, "Gemini Response with Hint (Task 3)"] = f"Error: {e}"
        print("✅ Gemini Response with Hint generated")

    # Without Hint (Search column)
    try:
        response_search = client.models.generate_content(
            model=model,
            contents=contents_task1
        )
        df.loc[index, "Gemini Response with Search (Task 3)"] = response_search.text.strip() if response_search.text else "(No answer returned)"
        print("✅ Gemini Response with Search generated")
    except Exception as e:
        df.loc[index, "Gemini Response with Search (Task 3)"] = f"Error: {e}"

    # With Hint & "Search"
    if row.get("Refined Prompt/Hint (Task 3)"):
        contents_search_hint = prepare_contents(row, use_hint=True)
        try:
            response_search_hint = client.models.generate_content(
                model=model,
                contents=contents_search_hint
            )
            df.loc[index, "Gemini Response with Search & Hint (Task 3)"] = response_search_hint.text.strip() if response_search_hint.text else "(No answer returned)"
        except Exception as e:
            df.loc[index, "Gemini Response with Search & Hint (Task 3)"] = f"Error: {e}"
        print("✅ Gemini Response with Search & Hint generated")

# ==================================================
# 7️⃣ Save updated Excel file
# ==================================================
output_path = "physics_questions_with_responses.xlsx"
df.to_excel(output_path, index=False)
print(f"\n🎉 Done! All responses saved to: {output_path}")
