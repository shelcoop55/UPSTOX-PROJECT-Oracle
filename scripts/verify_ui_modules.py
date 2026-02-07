
import sys
import os
import importlib
from pathlib import Path
from nicegui import ui

# Add project root to path
sys.path.append(os.getcwd())

def check_modules():
    print("Checking frontend/pages modules for import side effects...")
    
    pages_dir = Path("frontend/pages")
    modules = [f.stem for f in pages_dir.glob("*.py") if f.name != "__init__.py"]
    
    issues_found = []
    
    # We will try to import each module. 
    # If a module attempts to create a UI element at module level (without a page context), 
    # NiceGUI usually raises a RuntimeError (unless strict mode disabled or default page active).
    # Since we are running as script without `ui.run`, there is no context.
    
    for mod_name in modules:
        try:
            fullname = f"frontend.pages.{mod_name}"
            if fullname in sys.modules:
                continue
                
            # print(f"Testing import: {fullname}")
            try:
                importlib.import_module(fullname)
            except Exception as e:
                msg = str(e)
                # Specific errors indicating UI code ran outside context
                if "context" in msg.lower() or "nicegui" in msg.lower() or "page" in msg.lower():
                    print(f"🚨 ALERT: {mod_name} crashed on import: {e}")
                    issues_found.append(mod_name)
                else:
                    # Ignore unrelated errors (missing deps etc) unless obvious
                    # print(f"INFO: {mod_name} import error: {e}")
                    pass
            
        except Exception as outer_e:
            print(f"Outer error: {outer_e}")
    
    if issues_found:
        print("\nPossible culprits found:")
        for m in issues_found:
            print(f" - {m}")
    else:
        print("\n✅ No obvious UI execution detected during import.")

if __name__ == "__main__":
    check_modules()
