import os
from pathlib import Path

def image_generate():
    import tkinter as tk
    import customtkinter as ctk
    from PIL import Image, ImageTk
    import torch
    from diffusers import StableDiffusionPipeline
    try:
        from engine.authtoken import auth_token
    except ImportError:
        from authtoken import auth_token

    # Create the app
    app = tk.Tk()
    app.geometry("532x632")
    app.title("Stable Bud")
    ctk.set_appearance_mode("dark")

    # Prompt entry
    prompt = ctk.CTkEntry(
        master=app,
        height=40,
        width=512,
        font=("Arial", 20),
        text_color="black",
        fg_color="white"
    )
    prompt.place(x=10, y=10)

    # Label to show image
    lmain = ctk.CTkLabel(master=app, height=512, width=512, text="")
    lmain.place(x=10, y=110)

    # Model config for CPU
    modelid = "CompVis/stable-diffusion-v1-4"

    pipe = StableDiffusionPipeline.from_pretrained(
        modelid,
        torch_dtype=torch.float32,
        use_auth_token=auth_token
    )
    pipe.to("cpu")

    # Generate image function
    def generate():
        text = prompt.get()
        if not text:
            return
        image = pipe(text, guidance_scale=8.5).images[0]
        pictures_folder = Path.home() / "Pictures"
        pictures_folder.mkdir(parents=True, exist_ok=True)
        image_path = pictures_folder / "generatedimage.png"
        image.save(str(image_path))
        img = ImageTk.PhotoImage(image)
        lmain.configure(image=img)
        lmain.image = img

    # Generate button
    trigger = ctk.CTkButton(
        master=app,
        height=40,
        width=120,
        font=("Arial", 20),
        text_color="white",
        fg_color="blue",
        text="Generate",
        command=generate
    )
    trigger.place(x=206, y=60)

    # Run app
    app.mainloop()

if __name__ == "__main__":
    image_generate()
