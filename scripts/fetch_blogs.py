import requests
import psycopg2

API_KEY = "0e609f61479b451ea6368d1bb690be9d"

# Your list of keyword sets
specialty_keywords = [
["depression", "anxiety", "stress", "mood swings", "hallucinations"],
    ["ear pain", "throat pain", "sinus", "hearing loss", "blocked nose"],
    ["sexual dysfunction", "infertility", "libido issues"],
    ["toothache", "cavity", "gum bleeding", "dental pain"],
    ["acne", "rash", "itching", "hair fall", "skin infection"],
    ["swelling", "fatigue", "blood in urine", "high blood pressure"],
    ["frequent urination", "thirst", "weight loss", "fatigue"],
    ["fever in kids", "child sick", "cough in children", "growth issues"],
    ["fever", "cough", "diarrhea", "vomiting", "rashes"],
    ["urinary tract infection", "blood in urine", "frequent urination", "kidney stones"],
    ["chest pain", "shortness of breath", "palpitations"],
    ["abdominal pain", "nausea", "vomiting", "constipation", "diarrhea"],
    ["pregnancy care", "menstrual problems", "infertility", "menopause"],
    ["back pain", "neck pain", "joint pain", "chronic pain"],
    ["general health issues", "preventive care", "vaccinations"],
    ["seizures", "developmental delay", "muscle weakness"],
    ["blurred vision", "red eyes", "eye pain", "cataract"],
    ["morbid obesity", "weight gain", "diabetes due to obesity"],
    ["chronic pain", "allergies", "stress"],
    ["surgery preparation", "anesthesia consultation"],
    ["cancer lump", "tumor pain", "weight loss"]
]

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="medbot",
    user="postgres",
    password="dashboard",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

for keywords in specialty_keywords:
    used_words = set()  # track duplicates within this set
    for word in keywords:
        if word in used_words:
            continue
        used_words.add(word)

        print(f"Fetching blogs for: {word}")
        url = f"https://newsapi.org/v2/everything?q={word}&language=en&pageSize=3&apiKey={API_KEY}"
        response = requests.get(url).json()

        for article in response.get("articles", []):
            heading = article.get("title")
            description = article.get("description")
            link = article.get("url")
            published_at = article.get("publishedAt")
            source = article.get("source", {}).get("name")

            if heading and link:  # basic check
                cur.execute("""
                    INSERT INTO blogs (specialty, title, description, url, published_at, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (word, heading, description, link, published_at, source))

        conn.commit()

cur.close()
conn.close()
print("✅ Blogs fetched for all specialties and saved to Postgres!")
