import os
import shutil
import tempfile
from huggingface_hub import HfApi, login

def deploy():
    print("="*60)
    # 1. Gather User Inputs
    username = input("Enter your Hugging Face Username: ").strip()
    token = input("Enter your Hugging Face API WRITE Token: ").strip()
    space_name = input("Enter desired Space Name [default: shg-guardian-ai]: ").strip()
    
    if not space_name:
        space_name = "shg-guardian-ai"
        
    repo_id = f"{username}/{space_name}"
    
    # 2. Login to Hugging Face Hub
    try:
        print("\n[INFO] Authenticating with Hugging Face...")
        login(token)
        api = HfApi()
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return

    # 3. Create Space Repo on Hugging Face
    try:
        print(f"[INFO] Creating Hugging Face Space: {repo_id}...")
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="gradio",
            private=False,
            exist_ok=True
        )
        print(f"[SUCCESS] Repository {repo_id} created or verified.")
    except Exception as e:
        print(f"[ERROR] Failed to create Space repository: {e}")
        return

    # 4. Generate README.md with Hugging Face configuration frontmatter metadata
    # Spaces require YAML metadata headers in README.md to know which file to execute
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    readme_src_path = os.path.join(workspace_dir, "README.md")
    
    # We will create a temporary directory to structure our Hugging Face space files 
    # to avoid checking in local cache/db files (.db, logs/, etc.)
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n[INFO] Packing project files...")
        
        # Copy folders
        folders_to_copy = ["agents", "core", "memory", "tools", "Sample_test_dat"]
        for folder in folders_to_copy:
            src = os.path.join(workspace_dir, folder)
            dst = os.path.join(temp_dir, folder)
            if os.path.exists(src):
                shutil.copytree(src, dst)
        
        # Copy core python files
        files_to_copy = ["app.py", "main_agent.py", "requirements.txt"]
        for file in files_to_copy:
            src = os.path.join(workspace_dir, file)
            dst = os.path.join(temp_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)

        # Create README with Spaces Metadata header
        hf_readme_content = f"""---
title: SHG Guardian AI
emoji: 🛡️
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 6.19.0
app_file: app.py
pinned: false
---

"""
        # Append existing README contents
        if os.path.exists(readme_src_path):
            with open(readme_src_path, "r", encoding="utf-8") as f:
                hf_readme_content += f.read()
        
        with open(os.path.join(temp_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(hf_readme_content)

        # 5. Upload files to Hugging Face Space
        print(f"[INFO] Uploading files to Hugging Face Spaces ({repo_id})...")
        try:
            api.upload_folder(
                folder_path=temp_dir,
                repo_id=repo_id,
                repo_type="space"
            )
            print("\n" + "="*60)
            print(f"🎉 SUCCESS! YOUR AGENT IS DEPLOYED TO HUGGING FACE SPACES!")
            print(f"Visit your Space here: https://huggingface.co/spaces/{repo_id}")
            print("="*60)
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")

if __name__ == "__main__":
    deploy()
