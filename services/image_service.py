import os
import time
import base64
import json
import threading
from datetime import datetime
from pathlib import Path
from services.api_service import aurex_api
from services.event_bus import bus
from database.database import get_connection
from authentication.session import current_session

IMAGES_DIR = Path("Aurex_Data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

class ImageService:
    def __init__(self):
        self._is_generating = False

    def generate(self, prompt, style, aspect_ratio, model, quality, n=1, reference_images=None):
        if self._is_generating:
            bus.publish("IMAGE_GEN_ERROR", {"message": "Already generating an image."})
            return

        self._is_generating = True
        bus.publish("IMAGE_GEN_START", {"prompt": prompt})

        # Run in thread
        threading.Thread(target=self._generate_worker, args=(prompt, style, aspect_ratio, model, quality, n, reference_images), daemon=True).start()

    def _generate_worker(self, prompt, style, aspect_ratio, model, quality, n, reference_images):
        start_time = time.time()
        
        try:
            if not aurex_api.client:
                raise ValueError("API Client not initialized.")
                
            # 1. Mode Detection Engine
            generation_mode = "text_to_image"
            if reference_images:
                if len(reference_images) == 1:
                    if not prompt:
                        generation_mode = "enhance"
                    else:
                        generation_mode = "image_to_image"
                else:
                    generation_mode = "multi_reference"
                    
            print(f"[MODE] Detected generation mode: {generation_mode}")

            # 2. Vision Pipeline
            vision_prompt = None
            if generation_mode != "text_to_image":
                bus.publish("IMAGE_GEN_PROGRESS", {"status": "Analyzing reference images...", "progress": 15})
                b64_images = []
                for img_path in reference_images:
                    with open(img_path, "rb") as f:
                        b64_images.append(base64.b64encode(f.read()).decode('utf-8'))
                
                vision_instructions = ""
                if generation_mode == "enhance":
                    vision_instructions = "Describe this image in extreme detail so it can be perfectly recreated and enhanced. Focus on the core subjects, lighting, mood, color palette, and composition."
                elif generation_mode == "image_to_image":
                    vision_instructions = f"Analyze this image. The user wants to modify it with this instruction: '{prompt}'. Describe how the final image should look, combining the original image's core subject and layout with the user's new instructions."
                elif generation_mode == "multi_reference":
                    vision_instructions = f"Analyze these images. The user wants to combine them or use them as style references with this instruction: '{prompt}'. Synthesize a unified, highly detailed prompt that perfectly blends the visual style, color palette, and artistic characteristics of these images with the user's instructions."
                
                vision_prompt = aurex_api.vision_analysis(vision_instructions, b64_images)
                print(f"[VISION] Prompt generated: {vision_prompt[:100]}...")
            
            # 3. Prompt Engine & Style Engine
            bus.publish("IMAGE_GEN_PROGRESS", {"status": "Constructing final prompt...", "progress": 35})
            
            base_prompt = vision_prompt if vision_prompt else prompt
            
            style_modifiers = ""
            if style and style != "None":
                if style == "Anime":
                    style_modifiers = "anime style, high quality illustration, vibrant colors, studio quality, 2d animation aesthetic"
                elif style == "Cyberpunk":
                    style_modifiers = "cyberpunk aesthetic, neon lights, futuristic environment, high tech, dystopian, vibrant reflections"
                elif style == "Sketch":
                    style_modifiers = "pencil sketch, concept art, hand drawn, rough lines, monochrome, expressive shading"
                elif style == "Realistic":
                    style_modifiers = "photorealistic, ultra detailed, cinematic lighting, 8k resolution, highly textured"
                elif style == "3D Render":
                    style_modifiers = "3D render, octane render, unreal engine 5, ray tracing, volumetric lighting, smooth textures"
                else:
                    style_modifiers = f"In the style of {style}"
                    
                print(f"[STYLE] {style} modifiers applied.")
            
            quality_modifiers = ""
            if quality == "Ultra":
                quality_modifiers = "masterpiece, award winning, best quality, ultra-detailed"
            elif quality == "High":
                quality_modifiers = "high resolution, detailed"
                
            # Construct Final
            parts = []
            if base_prompt: parts.append(base_prompt)
            if style_modifiers: parts.append(style_modifiers)
            if quality_modifiers: parts.append(quality_modifiers)
            
            enhanced_prompt = ", ".join(parts)
            
            # 4. Aspect Ratio Engine
            size = "1024x1024"
            if aspect_ratio == "16:9": size = "1344x768" if model in ["black-forest-labs/flux1-dev"] else "1024x576"
            elif aspect_ratio == "9:16": size = "768x1344" if model in ["black-forest-labs/flux1-dev"] else "576x1024"
            elif aspect_ratio == "4:3": size = "1152x864" if model in ["black-forest-labs/flux1-dev"] else "1024x768"
            elif aspect_ratio == "3:4": size = "864x1152" if model in ["black-forest-labs/flux1-dev"] else "768x1024"
            
            print(f"[GENERATION] Model: {model}, Size: {size}")
            bus.publish("IMAGE_GEN_PROGRESS", {"status": f"Generating with {model}...", "progress": 50})
            
            import requests
            if aurex_api.provider == "Nvidia API":
                model_name = "black-forest-labs/flux.1-dev"
                
                invoke_url = f"https://ai.api.nvidia.com/v1/genai/{model_name}"
                headers = {
                    "Authorization": f"Bearer {aurex_api.api_key}",
                    "Accept": "application/json",
                }
                payload = {
                    "prompt": enhanced_prompt,
                    "seed": 42
                }
                res = requests.post(invoke_url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise Exception(f"NVIDIA API Error: {res.text}")
                    
                json_data = res.json()
                b64_data = json_data.get("image")
                if not b64_data:
                    b64_data = json_data.get("b64_json")
                if not b64_data and json_data.get("artifacts"):
                    b64_data = json_data.get("artifacts")[0].get("base64")
                    
                if not b64_data:
                    raise Exception("No image returned from NVIDIA API.")
            else:
                response = aurex_api.client.images.generate(
                    model=model,
                    prompt=enhanced_prompt,
                    n=int(n),
                    size=size,
                    response_format="b64_json"
                )
                b64_data = response.data[0].b64_json
            image_data = base64.b64decode(b64_data)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Aurex_{timestamp}.png"
            
            year_dir = IMAGES_DIR / str(datetime.now().year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = year_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_data)
                
            w, h = 1024, 1024
            if "x" in size:
                w, h = map(int, size.split("x"))
                
            gen_time = time.time() - start_time
            
            user_id = current_session.user_id if current_session.user_id else 1
            ref_json = json.dumps(reference_images) if reference_images else None
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO image_history 
                (user_id, prompt, style, aspect_ratio, model, quality, local_path, generation_type, width, height, generation_time, reference_images, vision_prompt, generation_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, prompt, style, aspect_ratio, model, quality, str(filepath), "generate", w, h, gen_time, ref_json, vision_prompt, generation_mode))
            conn.commit()
            
            row_id = cursor.lastrowid
            conn.close()
            
            bus.publish("IMAGE_GEN_SUCCESS", {
                "id": row_id,
                "filepath": str(filepath),
                "generation_time": gen_time,
                "generation_mode": generation_mode
            })
            bus.publish("HISTORY_UPDATED", {})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            bus.publish("IMAGE_GEN_ERROR", {"message": str(e)})
        finally:
            self._is_generating = False

    def get_history(self, limit=20):
        user_id = current_session.user_id if current_session.user_id else 1
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM image_history 
            WHERE user_id = ? AND generation_type = 'generate'
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def delete_history_item(self, history_id):
        user_id = current_session.user_id if current_session.user_id else 1
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT local_path FROM image_history WHERE id = ? AND user_id = ?", (history_id, user_id))
        row = cursor.fetchone()
        if row:
            try:
                if os.path.exists(row['local_path']):
                    os.remove(row['local_path'])
            except:
                pass
                
            cursor.execute("DELETE FROM image_history WHERE id = ? AND user_id = ?", (history_id, user_id))
            conn.commit()
            bus.publish("HISTORY_UPDATED", {})
            
        conn.close()

# Global singleton
image_service = ImageService()
