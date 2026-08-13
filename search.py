import json
import sqlite3
import math
from ingest import get_embedding

def cosine_similarity(v1, v2):
    """İki vektör (koordinat) arasındaki anlamsal benzerliği hesaplar."""
    dot_product = sum(x * y for x, y in zip(v1, v2))
    magnitude1 = math.sqrt(sum(x * x for x in v1))
    magnitude2 = math.sqrt(sum(y * y for y in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def search_database(query):
    print(f"\nSoru: '{query}'")
    print("Soru vektöre dönüştürülüyor...")
    
    # 1. Kullanıcının sorusunu da koordinatlara çeviriyoruz
    query_vector = get_embedding(query)
    
    # 2. Veritabanındaki tüm belgeleri çekiyoruz
    conn = sqlite3.connect("rag_assistant.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()
    
    # 3. Sorunun koordinatı ile belgelerin koordinatlarını karşılaştırıyoruz
    best_score = -1
    best_match = None
    
    print("Veritabanında en yakın bilgi aranıyor...")
    for row in rows:
        content = row[0]
        doc_vector = json.loads(row[1])
        
        # Kosinüs benzerliği ile aradaki mesafeyi ölçüyoruz
        score = cosine_similarity(query_vector, doc_vector)
        
        if score > best_score:
            best_score = score
            best_match = content
            
    print(f"\n--- En İyi Eşleşme Bulundu (Benzerlik Skoru: {best_score:.4f}) ---")
    print(best_match)
    print("----------------------------------------------------------\n")

if __name__ == "__main__":
    # Asistanımıza veritabanındaki bilgiyle eşleşebilecek bir soru soruyoruz
    soru = "What is the main advantage of using Microsoft Foundry Local?"
    search_database(soru)