import torch
import torch.nn as nn
import clip
from PIL import Image
from torchvision import transforms
import os
import json  # ### REVISI 1: JANGAN LUPA IMPORT INI
from app.config import MODEL_PATH 

# --- 1. DEFINISI ARSITEKTUR ---
class CLIPFineTuner(nn.Module):
    def __init__(self, model, class_names):
        super().__init__()
        self.model = model
        input_dim = model.visual.output_dim
        self.classifier = nn.Sequential(
            nn.Dropout(0.5), 
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(512, len(class_names))
        )

    def forward(self, x):
        features = self.model.encode_image(x)
        return self.classifier(features)

# --- 2. SERVICE CLASS ---
class CLIPService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_instance = None
        self.preprocess = None
        self.genres = [] # ### REVISI 2: Kosongkan list ini dulu
        self.weights_path = MODEL_PATH
        
        # ### REVISI 3: LOGIKA PATH RELATIF YANG BENAR
        # 1. Ambil lokasi file ini berada (.../app/services/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Mundur satu folder ('..') ke 'app', lalu masuk ke 'weights', lalu ambil json-nya
        # Hasilnya jadi: .../app/weights/class_mapping.json
        self.mapping_path = os.path.join(current_dir, '..', 'weights', 'class_mapping.json')

    def load_model(self):
        if self.model_instance is not None:
            return

        print(f"[CLIP Service] Memuat model...")
        
        # ### REVISI 4: LOAD JSON MAPPING (SEBELUM LOAD MODEL)
        if os.path.exists(self.mapping_path):
            try:
                print(f"[CLIP Service] Membaca mapping dari: {self.mapping_path}")
                with open(self.mapping_path, 'r') as f:
                    mapping = json.load(f)
                    # Pastikan urutan list sesuai index 0, 1, 2
                    # JSON key itu string ("0", "1"), jadi harus kita urutkan
                    self.genres = [mapping[str(i)] for i in range(len(mapping))]
                print(f"[CLIP Service] Label berhasil dimuat: {self.genres}")
            except Exception as e:
                print(f"[CLIP Service] Error baca JSON: {e}. Menggunakan default.")
                self.genres = ["expressionism", "impressionism", "surrealism"]
        else:
            print(f"[CLIP Service] WARNING: {self.mapping_path} tidak ditemukan. Menggunakan default.")
            self.genres = ["expressionism", "impressionism", "surrealism"]

        # --- LANJUT LOAD CLIP SEPERTI BIASA ---
        try:
            print(f"[CLIP Service] Memuat weights dari: {self.weights_path}")
            base_model, _ = clip.load("ViT-B/32", device=self.device, jit=False)
            base_model = base_model.float()

            self.preprocess = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize((0.48145466, 0.4578275, 0.40821073), 
                                     (0.26862954, 0.26130258, 0.27577711))
            ])
            
            # Masukkan self.genres yang sudah di-load dari JSON
            self.model_instance = CLIPFineTuner(base_model, self.genres).to(self.device)

            if os.path.exists(self.weights_path):
                state_dict = torch.load(self.weights_path, map_location=self.device)
                self.model_instance.load_state_dict(state_dict)
                self.model_instance.eval()
                print("[CLIP Service] Model berhasil dimuat!")
            else:
                print(f"[CLIP Service] ERROR: File {self.weights_path} tidak ditemukan!")
                self.model_instance = None
                
        except Exception as e:
            print(f"[CLIP Service] Critical Error loading model: {e}")
            self.model_instance = None

    def predict_image(self, image_path):
        if self.model_instance is None:
            self.load_model()
            if self.model_instance is None:
                return {"label": "System Error", "confidence": "0%"}

        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                base_clip = self.model_instance.model 
                
                # ==========================================================
                # 1. FILTER: OOD CHECK (DENGAN LOGIKA "SIBLING CHECK")
                # ==========================================================
                target_prompts = [f"a {genre} painting" for genre in self.genres]
                
                # Daftar Noise Lengkap (Termasuk Fauvism dll)
                noise_prompts = [
                    "Abstract Expressionism painting", "Action painting", "Analytical Cubism painting",
                    "Art Nouveau Modern Art", "Baroque painting", "Color Field Painting",
                    "Contemporary Realism painting", "Cubism painting", "Early Renaissance painting",
                    "Fauvism painting", "High Renaissance painting", "Mannerism Late Renaissance painting",
                    "Minimalism art", "Naive Art Primitivism", "New Realism painting",
                    "Northern Renaissance painting", "Pointillism painting", "Pop Art",
                    "Post Impressionism painting", "Realism painting", "Rococo painting",
                    "Romanticism painting", "Symbolism painting", "Synthetic Cubism painting",
                    "Ukiyo-e print",
                    "a photograph", "anime style", "sketch or drawing", "vector logo", "3d render", "cartoon"
                ]
                
                all_prompts = target_prompts + noise_prompts
                text_inputs = clip.tokenize(all_prompts).to(self.device)
                
                image_features = base_clip.encode_image(image_tensor)
                text_features = base_clip.encode_text(text_inputs)
                
                image_features_norm = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features_norm = text_features / text_features.norm(dim=-1, keepdim=True)
                
                similarity = (100.0 * image_features_norm @ text_features_norm.T).softmax(dim=-1)
                top_prob, top_idx = similarity[0].topk(1)
                best_match_index = top_idx.item()
                
                # Variable Flag untuk menandai apakah gambar ini "Mencurigakan" tapi boleh lanjut
                is_ambiguous_pass = False 

                # --- LOGIKA MODIFIKASI ---
                if best_match_index >= len(target_prompts):
                      detected_noise = all_prompts[best_match_index]
                      
                      # DAFTAR ALIRAN YANG MIRIP EXPRESSIONISM (SAUDARA KANDUNG)
                      sibling_styles = [
                          "Fauvism", "Abstract Expressionism", "Post Impressionism", "Symbolism", "Naive Art Primitivism"
                      ]
                      
                      is_sibling = any(s in detected_noise for s in sibling_styles)
                      
                      if is_sibling:
                          print(f"[Filter] Terdeteksi mirip {detected_noise}, tapi mungkin Expressionism. Cek ulang...")
                          is_ambiguous_pass = True
                      else:
                          print(f"[Filter Active] Ditolak mutlak. Terdeteksi sebagai: {detected_noise}")
                          return {"label": "Unknown Art Style", "confidence": "Low"}

                # ==========================================================
                # 2. PREDIKSI UTAMA (FINE-TUNED CLASSIFIER)
                # ==========================================================
                logits = self.model_instance(image_tensor) 
                probs = torch.nn.functional.softmax(logits, dim=1)
                top_prob, top_idx = torch.max(probs, 1)

            label = self.genres[top_idx.item()]
            confidence = top_prob.item() * 100

            # ==========================================================
            # 3. PENENTUAN AKHIR (FINAL GATEKEEPER)
            # ==========================================================
            
            # SKENARIO A: Gambar lolos "Soft Pass"
            if is_ambiguous_pass:
                if confidence < 70.0:
                    result = {"label": "Unknown Art Style", "confidence": "Low (Ambiguous)"}
                    print(f"[Terminal Result] {result['label']} | Conf: {confidence:.2f}%") # <-- TAMBAHAN
                    return result
                else:
                    pass 

            # SKENARIO B: Gambar normal
            else:
                if confidence < 60.0:
                    result = {"label": "Unknown Image", "confidence": f"{confidence:.1f}%"}
                    print(f"[Terminal Result] {result['label']} | Conf: {confidence:.1f}%") # <-- TAMBAHAN
                    return result

            # HASIL BERHASIL
            final_label = label.title()
            final_conf = f"{confidence:.1f}%"
            
            # --- TAMPILKAN DI TERMINAL ---
            print("-" * 30)
            print(f"PREDIKSI BERHASIL!")
            print(f"Gambar    : {os.path.basename(image_path)}")
            print(f"Aliran Art: {final_label}")
            print(f"Confidence: {final_conf}")
            print("-" * 30)

            return {
                "label": final_label,
                "confidence": final_conf
            }

        except Exception as e:
            print(f"Error prediction: {e}")
            import traceback
            traceback.print_exc()
            return {"label": "Error", "confidence": "0%"}

clip_service = CLIPService()