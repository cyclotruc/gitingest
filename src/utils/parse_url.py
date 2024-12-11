
import uuid

from config import TMP_BASE_PATH

def parse_url(url: str) -> dict:
    parsed = {
        
        "user_name": None,
        "repo_name": None,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": None,
        "url": None,
    }
    
    
    if not url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    
    
    
    # Remove anything after the first space
    url = url.split(" ")[0]

    url = url.replace("https://github.com/", "")
    path_parts = url.split('/')

    parsed["user_name"] = path_parts[0]
    parsed["repo_name"] = path_parts[1]
    

    parsed["url"] = f"https://github.com/{parsed['user_name']}/{parsed['repo_name']}"
    parsed['slug'] = parsed["url"].replace("https://github.com/", "").replace("/", "-")
    parsed["id"] = str(uuid.uuid4())
    parsed["local_path"] = f"{TMP_BASE_PATH}/{parsed['id']}/{parsed['slug']}"
    

    if len(path_parts) > 3:
        parsed["type"] = path_parts[2]
        parsed["branch"] = path_parts[3]
        if len(parsed['branch']) == 40 and all(c in '0123456789abcdefABCDEF' for c in parsed['branch']):
            parsed["commit"] = parsed['branch']
            
        parsed["subpath"] = "/" + "/".join(path_parts[4:])
    return parsed